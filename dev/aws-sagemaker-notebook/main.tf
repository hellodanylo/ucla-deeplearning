terraform {
  required_providers {
    aws = {
      version = "4.30.0"
    }
  }

  backend "s3" {}
}

variable "notebook_name" {
  type = string
}

variable "instance_type" {
  type = string
}

variable "volume_size_gb" {
  type = number
}

variable "member_name" {
  type = string
}

variable "sagemaker_config" {
  type = object({
    lifecycle_config_name = string
    code_repository_name = string
    security_group_id = string
    subnet_id = string
  })
}

data "aws_caller_identity" "current" {}

resource "aws_iam_role" "sagemaker" {
  # The lifecycle script expects the role name to match the notebook name
  name               = var.notebook_name
  assume_role_policy = templatefile("${path.module}/sagemaker_assume_role.json", {
    aws_account_id = data.aws_caller_identity.current.account_id
  })
}

resource "aws_iam_policy" "sagemaker" {
  policy = file("${path.module}/policy.json")
  name = var.notebook_name
}

resource "aws_iam_role_policy_attachment" "sagemaker" {
  role       = aws_iam_role.sagemaker.name
  policy_arn = aws_iam_policy.sagemaker.arn
}

resource "aws_sagemaker_notebook_instance" "notebook" {
  name          = var.notebook_name
  role_arn      = aws_iam_role.sagemaker.arn
  instance_type = var.instance_type
  default_code_repository = var.sagemaker_config.code_repository_name
  volume_size = var.volume_size_gb
  subnet_id = var.sagemaker_config.subnet_id
  security_groups = [var.sagemaker_config.security_group_id]
  lifecycle_config_name = var.sagemaker_config.lifecycle_config_name
  platform_identifier = "notebook-al1-v1"

  tags = {
    Name = var.notebook_name
    Member = var.member_name
    owner = var.member_name
  }

  lifecycle {
    ignore_changes = [instance_type]
  }
}

output "notebook_name" {
  value = var.notebook_name
}
