resource "aws_cloudwatch_log_group" "backend" {
  name              = "/${var.project_name}/${var.environment}/backend"
  retention_in_days = 7
}


resource "aws_iam_policy" "cloudwatch_logs" {
  name = "${var.project_name}-${var.environment}-cloudwatch-logs"

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]

        Resource = "${aws_cloudwatch_log_group.backend.arn}:*"
      }
    ]
  })
}


resource "aws_iam_role_policy_attachment" "cloudwatch_logs" {
  role       = aws_iam_role.stayops_ec2.name
  policy_arn = aws_iam_policy.cloudwatch_logs.arn
}