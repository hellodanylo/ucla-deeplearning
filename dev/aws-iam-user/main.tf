terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "3.53.0"
    }
  }

  backend "s3" {}
}

variable "member" {
  type = object({
    name = string
    email = string
  })
}

variable "team" {
  type = object({
    admin_account_id = string
  })
}

resource "aws_iam_user" "user" {
  name = var.member.name
}

resource "aws_iam_access_key" "key" {
  user = aws_iam_user.user.name
}

data "aws_caller_identity" "current" {}

resource "aws_iam_role" "role" {
  # The lifecycle script expects the role name to match the notebook name
  name               = var.member.name
  assume_role_policy = templatefile("${path.module}/assume.json", {
    aws_account_id = var.team.admin_account_id
  })
}

resource "aws_iam_policy" "policy" {
  name = var.member.name
  policy = templatefile("${path.module}/policy.json", {
    user_name = aws_iam_user.user.name
  })
}

resource "aws_iam_user_policy_attachment" "user" {
  policy_arn = aws_iam_policy.policy.arn
  user = aws_iam_user.user.name
}

resource "aws_iam_role_policy_attachment" "role" {
  policy_arn = aws_iam_policy.policy.arn
  role = aws_iam_role.role.name
}

data "local_file" "pgp_key" {
  filename = "${path.module}/../pgp_public.key"
}

resource "aws_iam_user_login_profile" "login" {
  pgp_key = data.local_file.pgp_key.content_base64
  user = aws_iam_user.user.name
  password_reset_required = false
}

output "aws_access_key_id" {
  value = aws_iam_access_key.key.id
}

output "aws_access_key_secret" {
  value = aws_iam_access_key.key.secret
}

output "aws_login_username" {
  value = var.member.name
}

output "aws_login_password" {
  value = aws_iam_user_login_profile.login.encrypted_password
}