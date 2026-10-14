data "aws_caller_identity" "current" {}

# ──────────────────────── S3 bucket ────────────────────────
resource "aws_s3_bucket" "frontend" {
  # Bucket names are globally unique across all of AWS, so the account
  # ID is appended to avoid collisions with anyone else's.
  bucket = "${local.name_prefix}-frontend-${data.aws_caller_identity.current.account_id}"

  # Lets destroy delete the bucket even with objects in it.
  force_destroy = true

  tags = {
    Name = "${local.name_prefix}-frontend"
  }
}

# Belt and braces: the bucket is never publicly readable. CloudFront
# reaches it through OAC, not through public access.
resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ──────────────── Origin Access Control ────────────────
# An identity CloudFront uses to sign requests to S3. Replaces the older
# Origin Access Identity; this is the current approach.
resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "${local.name_prefix}-frontend-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# Allows exactly one thing: this distribution reading objects from this
# bucket. The SourceArn condition is what prevents someone else's
# CloudFront distribution from being pointed at your bucket.
data "aws_iam_policy_document" "frontend_bucket" {
  statement {
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.frontend.arn}/*"]

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.main.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  policy = data.aws_iam_policy_document.frontend_bucket.json
}

# ───────────── managed policies, looked up by name ─────────────
# Using data sources rather than hardcoded UUIDs, which is what most
# tutorials do and what makes their configs unreadable.
data "aws_cloudfront_cache_policy" "optimized" {
  name = "Managed-CachingOptimized"
}

data "aws_cloudfront_cache_policy" "disabled" {
  name = "Managed-CachingDisabled"
}

data "aws_cloudfront_origin_request_policy" "all_viewer_except_host" {
  name = "Managed-AllViewerExceptHostHeader"
}

locals {
  s3_origin_id  = "s3-frontend"
  alb_origin_id = "alb-api"

  # Every path the API owns. Anything not listed here falls through to
  # the S3 default behavior and serves the SPA.
  #
  # Adding a router in FastAPI means adding a pattern here. That coupling
  # is the cost of this approach; see the note below for the alternative.
  api_behaviors = [
    { pattern = "/auth/*", compress = true },
    { pattern = "/sessions*", compress = true },
    { pattern = "/questions*", compress = true },
    { pattern = "/health", compress = true },
    { pattern = "/metrics", compress = true },
    { pattern = "/docs*", compress = true },
    { pattern = "/openapi.json", compress = true },

    # SSE. Edge compression can buffer a streaming response, which would
    # defeat the point of streaming, so it's off for this one.
    { pattern = "/jobs/*", compress = false },
  ]
}

# ───────────────── CloudFront distribution ─────────────────
resource "aws_cloudfront_distribution" "main" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  comment             = "${local.name_prefix} app and api"

  # US, Canada, and Europe edges only — the cheapest tier. PriceClass_All
  # adds Asia, South America, and Oceania at higher per-GB rates.
  price_class = "PriceClass_100"

  origin {
    origin_id                = local.s3_origin_id
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  origin {
    origin_id   = local.alb_origin_id
    domain_name = aws_lb.main.dns_name

    custom_origin_config {
      http_port  = 80
      https_port = 443

      # CloudFront → ALB over plain HTTP, because the ALB has no
      # certificate. Viewer → CloudFront is still HTTPS. Documented in
      # 14.14 as a gap: a real deployment terminates TLS twice.
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # Everything not matched by an ordered behavior: the static app.
  default_cache_behavior {
    target_origin_id       = local.s3_origin_id
    viewer_protocol_policy = "redirect-to-https"

    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods  = ["GET", "HEAD"]
    compress        = true

    # Respects the Cache-Control headers set at upload time.
    cache_policy_id = data.aws_cloudfront_cache_policy.optimized.id
  }

  dynamic "ordered_cache_behavior" {
    for_each = local.api_behaviors

    content {
      path_pattern           = ordered_cache_behavior.value.pattern
      target_origin_id       = local.alb_origin_id
      viewer_protocol_policy = "redirect-to-https"

      allowed_methods = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
      cached_methods  = ["GET", "HEAD"]
      compress        = ordered_cache_behavior.value.compress

      # Never cache API responses.
      cache_policy_id = data.aws_cloudfront_cache_policy.disabled.id

      # Forward every header, cookie, and query param to the ALB except
      # Host. Required for Authorization, your refresh cookie, and
      # Idempotency-Key to reach FastAPI at all.
      origin_request_policy_id = data.aws_cloudfront_origin_request_policy.all_viewer_except_host.id
    }
  }

  # ── The SPA fix ──
  # S3 returns 403 (OAC, object missing) or 404 for /dashboard, because
  # no such object exists. Rewrite both to index.html with a 200 so the
  # bundle loads and React Router resolves the path client-side.
  custom_error_response {
    error_code            = 403
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 0
  }

  custom_error_response {
    error_code            = 404
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 0
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # Free certificate on the *.cloudfront.net domain. This is what gives
  # you real HTTPS without owning a domain.
  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Name = "${local.name_prefix}-cdn"
  }
}