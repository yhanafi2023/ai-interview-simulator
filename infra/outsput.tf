output "ecr_repository_url" {
  description = "Registry URL to docker push the backend image to."
  value       = aws_ecr_repository.backend.repository_url
}