# ─────────────────────── log groups ───────────────────────
# Must exist before a task starts, or the awslogs driver fails
# and the container never runs.
resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${local.name_prefix}-api"
  retention_in_days = 7 # without this, logs are kept forever and billed forever
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/ecs/${local.name_prefix}-worker"
  retention_in_days = 7
}

# ───────────────────────── cluster ─────────────────────────
resource "aws_ecs_cluster" "main" {
  name = "${local.name_prefix}-cluster"

  setting {
    name = "containerInsights"
    # Enabled, this publishes custom CloudWatch metrics that cost real money.
    # Not worth it for a stack that lives one afternoon.
    value = "disabled"
  }
}

# ────────────── shared config for both containers ──────────────
locals {
  # Non-secret configuration. Visible in the console; that's fine.
  app_environment = [
    { name = "ENVIRONMENT", value = var.environment },
    { name = "RELEASE", value = var.image_tag },
    { name = "JSON_LOGS", value = "true" },
    { name = "LOG_LEVEL", value = "INFO" },
    {
      name  = "REDIS_URL"
      value = "redis://${aws_elasticache_cluster.main.cache_nodes[0].address}:6379/0"
    },
    # Your local Vite dev server, so you can point the real frontend at
    # this API during verification in 14.11.
    { name = "CORS_ORIGINS", value = "http://localhost:5173" },
  ]

  # Secret configuration. ARNs only — the values are fetched at startup
  # by the execution role and never appear in this task definition.
  app_secrets = [
    { name = "DATABASE_URL", valueFrom = aws_secretsmanager_secret.database_url.arn },
    { name = "JWT_SECRET", valueFrom = aws_secretsmanager_secret.jwt_secret.arn },
    { name = "ANTHROPIC_API_KEY", valueFrom = aws_secretsmanager_secret.anthropic_api_key.arn },
  ]
}

# ─────────────────── API task definition ───────────────────
resource "aws_ecs_task_definition" "api" {
  family                   = "${local.name_prefix}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"

  cpu    = 256 # 0.25 vCPU
  memory = 512 # MB

  execution_role_arn = aws_iam_role.ecs_execution.arn
  task_role_arn      = aws_iam_role.ecs_task.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64" # must match the image you built in 14.7
  }

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = "${aws_ecr_repository.backend.repository_url}:${var.image_tag}"
      essential = true

      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      environment = local.app_environment
      secrets     = local.app_secrets

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.api.name
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = "api"
        }
      }
    }
  ])
}

# ────────────────── worker task definition ──────────────────
resource "aws_ecs_task_definition" "worker" {
  family                   = "${local.name_prefix}-worker"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"

  cpu    = 256
  memory = 512

  execution_role_arn = aws_iam_role.ecs_execution.arn
  task_role_arn      = aws_iam_role.ecs_task.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode([
    {
      name      = "worker"
      image     = "${aws_ecr_repository.backend.repository_url}:${var.image_tag}"
      essential = true

      # Same image, different command. No portMappings — nothing connects
      # to the worker; it pulls jobs from Redis.
      command = ["python", "-m", "app.worker"]

      environment = local.app_environment
      secrets     = local.app_secrets

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.worker.name
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = "worker"
        }
      }
    }
  ])
}

# ──────────────────── worker service ────────────────────
resource "aws_ecs_service" "worker" {
  name            = "${local.name_prefix}-worker"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  # Enables `aws ecs execute-command` — a shell inside the running task.
  # This is what the SSM permissions on the task role in 14.6 were for.
  enable_execute_command = true

  network_configuration {
    subnets         = aws_subnet.public[*].id
    security_groups = [aws_security_group.ecs_tasks.id]

    # REQUIRED. With no NAT Gateway, a public IP is the task's only route
    # to ECR, Secrets Manager, and the Anthropic API. Set this to false and
    # the task fails at startup, unable to pull its own image.
    assign_public_ip = true
  }
}