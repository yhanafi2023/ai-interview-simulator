resource "aws_ecr_repository" "backend" {
  name = "${local.name_prefix}-backend"

  # A pushed tag can never be overwritten. sha-abc123 always means the same bytes.
  image_tag_mutability = "IMMUTABLE"

  # Lets `terraform destroy` delete the repo even when images are inside it.
  # Correct here because teardown is the plan; wrong in real production.
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }
}