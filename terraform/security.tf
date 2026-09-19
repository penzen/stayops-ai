data "aws_ec2_managed_prefix_list" "cloudfront" {
  name = "com.amazonaws.global.cloudfront.origin-facing"
}

resource "aws_security_group" "backend" {
  name        = "${var.project_name}-${var.environment}-backend"
  description = "StayOps backend security group"
  vpc_id      = data.aws_vpc.default.id

  tags = {
    Name = "${var.project_name}-${var.environment}-backend"
  }
}

# Only AWS CloudFront may reach FastAPI on port 8000.
resource "aws_vpc_security_group_ingress_rule" "cloudfront_to_backend" {
  security_group_id = aws_security_group.backend.id

  prefix_list_id = data.aws_ec2_managed_prefix_list.cloudfront.id

  from_port   = 8000
  to_port     = 8000
  ip_protocol = "tcp"

  description = "Allow CloudFront to reach StayOps API"
}

# EC2 needs outbound internet access for ECR, OpenAI, SSM, etc.
resource "aws_vpc_security_group_egress_rule" "backend_outbound" {
  security_group_id = aws_security_group.backend.id

  cidr_ipv4   = "0.0.0.0/0"
  ip_protocol = "-1"

  description = "Allow outbound traffic"
}