resource "aws_iam_role" "stayops_ec2" {
  name = "${var.project_name}-${var.environment}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Principal = {
          Service = "ec2.amazonaws.com"
        }

        Action = "sts:AssumeRole"
      }
    ]
  })
}


# Allow EC2 to pull the StayOps image from ECR.
resource "aws_iam_role_policy_attachment" "ecr_read" {
  role       = aws_iam_role.stayops_ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}


# Allows us to access the machine through AWS Systems Manager
# instead of exposing SSH to the internet.
resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.stayops_ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}


resource "aws_iam_instance_profile" "stayops_ec2" {
  name = "${var.project_name}-${var.environment}-ec2-profile"
  role = aws_iam_role.stayops_ec2.name
}