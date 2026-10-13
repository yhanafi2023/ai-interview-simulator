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