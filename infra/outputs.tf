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