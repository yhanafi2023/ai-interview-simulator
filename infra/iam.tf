# ── Trust policy, shared by both roles ──
# "The ECS tasks service is allowed to wear this hat."
data "aws_iam_policy_document" "ecs_tasks_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

# ══════════════ EXECUTION ROLE — used by the ECS agent ══════════════
resource "aws_iam_role" "ecs_execution" {
  name               = "${local.name_prefix}-ecs-execution"
  description        = "Used by the ECS agent to pull images, fetch secrets, and write logs."
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume.json
}

# AWS-managed policy: ECR pull + CloudWatch Logs write. Maintained by AWS.
resource "aws_iam_role_policy_attachment" "ecs_execution_managed" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Reading secrets is NOT in the managed policy. Scoped to these three ARNs only.
data "aws_iam_policy_document" "read_app_secrets" {
  statement {
    effect  = "Allow"
    actions = ["secretsmanager:GetSecretValue"]

    resources = [
      aws_secretsmanager_secret.database_url.arn,
      aws_secretsmanager_secret.jwt_secret.arn,
      aws_secretsmanager_secret.anthropic_api_key.arn,
    ]
  }
}

resource "aws_iam_role_policy" "ecs_execution_secrets" {
  name   = "read-app-secrets"
  role   = aws_iam_role.ecs_execution.id
  policy = data.aws_iam_policy_document.read_app_secrets.json
}

# ══════════════ TASK ROLE — used by your application code ══════════════
resource "aws_iam_role" "ecs_task" {
  name               = "${local.name_prefix}-ecs-task"
  description        = "Assumed by the application itself. Deliberately minimal."
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume.json
}

# Enables `aws ecs execute-command` — a shell inside a running task.
# These actions don't support resource-level scoping, so "*" is required
# rather than lazy. The real control is that only this role has them.
data "aws_iam_policy_document" "ecs_exec" {
  statement {
    effect = "Allow"
    actions = [
      "ssmmessages:CreateControlChannel",
      "ssmmessages:CreateDataChannel",
      "ssmmessages:OpenControlChannel",
      "ssmmessages:OpenDataChannel",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "ecs_task_exec" {
  name   = "allow-ecs-exec"
  role   = aws_iam_role.ecs_task.id
  policy = data.aws_iam_policy_document.ecs_exec.json
}