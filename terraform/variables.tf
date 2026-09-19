variable "aws_region" {
  description = "AWS region for StayOps"
  type        = string
  default     = "eu-central-1"
}

variable "project_name" {
  description = "Project name used for AWS resources"
  type        = string
  default     = "stayops"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "demo"
}

variable "ecr_repository_url" {
  description = "ECR repository containing the StayOps backend image"
  type        = string
  default     = "563683520024.dkr.ecr.eu-central-1.amazonaws.com/stayops-backend"
}

variable "image_tag" {
  description = "Immutable Docker image version"
  type        = string
  default     = "v2"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "m7i-flex.large"
}