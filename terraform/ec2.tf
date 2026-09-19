data "aws_ssm_parameter" "amazon_linux_2023" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

resource "aws_instance" "backend" {
  ami           = data.aws_ssm_parameter.amazon_linux_2023.value
  instance_type = var.instance_type

  subnet_id = sort(tolist(data.aws_subnets.default.ids))[0]

  associate_public_ip_address = true

  vpc_security_group_ids = [
    aws_security_group.backend.id
  ]

  iam_instance_profile = aws_iam_instance_profile.stayops_ec2.name


  user_data = templatefile(
    "${path.module}/user_data.sh.tftpl",
    {
      aws_region         = var.aws_region
      account_id         = data.aws_caller_identity.current.account_id
      ecr_repository_url = var.ecr_repository_url
      image_tag          = var.image_tag
      secret_name        = aws_secretsmanager_secret.openai.name
      log_group          = aws_cloudwatch_log_group.backend.name
    }
  )

  user_data_replace_on_change = true


  root_block_device {
    volume_type = "gp3"
    volume_size = 20
    encrypted   = true
  }


  metadata_options {
    http_endpoint = "enabled"

    # Require IMDSv2 rather than the older metadata protocol.
    http_tokens = "required"
  }


  tags = {
    Name = "${var.project_name}-${var.environment}-backend"
  }


  depends_on = [
    aws_iam_role_policy_attachment.ecr_read,
    aws_iam_role_policy_attachment.ssm,
    aws_iam_role_policy_attachment.read_openai_secret,
    aws_iam_role_policy_attachment.cloudwatch_logs,
    aws_cloudwatch_log_group.backend
  ]
}