resource "aws_secretsmanager_secret" "openai" {
  name = "${var.project_name}/${var.environment}/openai-api-key"

  description = "OpenAI API key used by StayOps"

  # Makes terraform destroy straightforward for this temporary demo stack.
  recovery_window_in_days = 0
}


resource "aws_iam_policy" "read_openai_secret" {
  name = "${var.project_name}-${var.environment}-read-openai-secret"

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Action = [
          "secretsmanager:GetSecretValue"
        ]

        Resource = aws_secretsmanager_secret.openai.arn
      }
    ]
  })
}


resource "aws_iam_role_policy_attachment" "read_openai_secret" {
  role       = aws_iam_role.stayops_ec2.name
  policy_arn = aws_iam_policy.read_openai_secret.arn
}