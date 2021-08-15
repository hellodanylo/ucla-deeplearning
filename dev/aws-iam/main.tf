terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "3.53.0"
    }
  }

  backend "s3" {}
}

variable "team" {
  type = object({
    admin_name = string,
    admin_account_id = string
  })
}

resource "aws_iam_user" "admin" {
  name = var.team.admin_name
}

resource "aws_iam_role" "admin" {
  name = var.team.admin_name
  assume_role_policy = templatefile("${path.module}/assume.json", {
    aws_account_id = var.team.admin_account_id
  })
}

resource "aws_iam_user_policy_attachment" "admin" {
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
  user = aws_iam_user.admin.name
}

resource "aws_iam_role_policy_attachment" "admin" {
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
  role = aws_iam_role.admin.name
}

resource "aws_iam_access_key" "key" {
  user = aws_iam_user.admin.name
}

output "aws_access_key_id" {
  value = aws_iam_access_key.key.id
  sensitive = true
}

output "aws_access_key_secret" {
  value = aws_iam_access_key.key.secret
  sensitive = true
}