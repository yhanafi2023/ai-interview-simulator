resource "aws_lb" "main" {
  name               = "${local.name_prefix}-alb"
  load_balancer_type = "application"
  internal           = false # internet-facing

  security_groups = [aws_security_group.alb.id]
  subnets         = aws_subnet.public[*].id # needs 2+ AZs, which is why 14.3 built two

  # How long an idle connection is held open. Your SSE endpoint sends a
  # keep-alive comment every second, so it never goes idle — but a value
  # comfortably above the keep-alive interval avoids surprises.
  idle_timeout = 120

  enable_deletion_protection = false # teardown-friendly; production says true

  tags = {
    Name = "${local.name_prefix}-alb"
  }
}

resource "aws_lb_target_group" "api" {
  name     = "${local.name_prefix}-api"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  # REQUIRED for Fargate. With awsvpc networking each task has its own IP,
  # so targets are IPs, not instance IDs. Using "instance" here fails.
  target_type = "ip"

  # How long to keep draining in-flight requests on a target being removed.
  # See the note below — this one has a direct tradeoff for your app.
  deregistration_delay = 60

  health_check {
    enabled  = true
    path     = "/health"
    protocol = "HTTP"
    matcher  = "200"

    interval            = 15 # probe every 15s
    timeout             = 5  # a probe taking >5s counts as a failure
    healthy_threshold   = 2  # 2 consecutive passes → healthy
    unhealthy_threshold = 3  # 3 consecutive failures → unhealthy
  }

  tags = {
    Name = "${local.name_prefix}-api-tg"
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}