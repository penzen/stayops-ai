output "backend_instance_id" {
  description = "StayOps EC2 instance ID"
  value       = aws_instance.backend.id
}

output "backend_public_dns" {
  description = "EC2 public DNS"
  value       = aws_instance.backend.public_dns
}

output "backend_https_url" {
  description = "Public HTTPS URL for StayOps API"
  value       = "https://${aws_cloudfront_distribution.backend.domain_name}"
}

output "cloudwatch_log_group" {
  description = "StayOps backend CloudWatch log group"
  value       = aws_cloudwatch_log_group.backend.name
}

output "ecr_image" {
  description = "Backend Docker image deployed to EC2"
  value       = "${var.ecr_repository_url}:${var.image_tag}"
}

output "frontend_bucket" {
  description = "StayOps frontend S3 bucket"
  value       = aws_s3_bucket.frontend.bucket
}

output "frontend_distribution_id" {
  description = "StayOps frontend CloudFront distribution ID"
  value       = aws_cloudfront_distribution.frontend.id
}

output "frontend_url" {
  description = "Public StayOps frontend URL"
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}