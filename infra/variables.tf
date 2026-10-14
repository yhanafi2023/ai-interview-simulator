variable "project" {
  description = "Short name prefixed onto every resource for identification."
  type        = string
  default     = "ai-interview"
}

variable "region" {
  description = "AWS region. us-east-1 is cheapest and is where billing metrics live."
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment. Appears in names and tags."
  type        = string
  default     = "dev"
}
variable "anthropic_api_key" {
  description = "Anthropic API key. Supply via TF_VAR_anthropic_api_key. Never commit."
  type        = string
  sensitive   = true
  # No default. Terraform will error if it's missing, which is the point.
}