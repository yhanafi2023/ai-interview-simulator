output "ecr_repository_url" {
  description = "Registry URL to docker push the backend image to."
  value       = aws_ecr_repository.backend.repository_url
}
output "vpc_id" {
  description = "ID of the project VPC."
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets, one per AZ."
  value       = aws_subnet.public[*].id
}

output "security_group_ids" {
  description = "Security group IDs by tier."
  value = {
    alb   = aws_security_group.alb.id
    tasks = aws_security_group.ecs_tasks.id
    rds   = aws_security_group.rds.id
    redis = aws_security_group.redis.id
  }
}

output "database_url" {
  description = "SQLAlchemy connection URL for the RDS instance."
  value = format(
    "postgresql+psycopg://%s:%s@%s/%s",
    aws_db_instance.main.username,
    random_password.db.result,
    aws_db_instance.main.endpoint, # already includes :5432
    aws_db_instance.main.db_name,
  )
  sensitive = true
}

output "redis_url" {
  description = "Redis connection URL for the ElastiCache node."
  value       = "redis://${aws_elasticache_cluster.main.cache_nodes[0].address}:6379/0"
}

output "iam_role_arns" {
  description = "ECS role ARNs, consumed by the task definitions in 14.8."
  value = {
    execution = aws_iam_role.ecs_execution.arn
    task      = aws_iam_role.ecs_task.arn
  }
}

output "secret_arns" {
  description = "Secret ARNs injected into containers at startup."
  value = {
    database_url      = aws_secretsmanager_secret.database_url.arn
    jwt_secret        = aws_secretsmanager_secret.jwt_secret.arn
    anthropic_api_key = aws_secretsmanager_secret.anthropic_api_key.arn
  }
}
output "api_url" {
  description = "Base URL of the API through the load balancer."
  value       = "http://${aws_lb.main.dns_name}"
}