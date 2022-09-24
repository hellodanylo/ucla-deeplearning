terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "4.30.0"
    }
  }

  backend "s3" {}
}

resource "aws_iam_user" "user" {
  name = "builder"
}

resource "aws_iam_access_key" "key" {
  user = aws_iam_user.user.name
}

data "aws_caller_identity" "current" {}

resource "aws_iam_policy" "policy" {
  name = aws_iam_user.user.name
  policy = templatefile("${path.module}/policy.json", {
    user_name = aws_iam_user.user.name
  })
}

resource "aws_iam_user_policy_attachment" "user" {
  policy_arn = aws_iam_policy.policy.arn
  user = aws_iam_user.user.name
}

data "local_file" "pgp_key" {
  filename = "${path.module}/../pgp_public.key"
}

output "aws_access_key_id" {
  value = aws_iam_access_key.key.id
}

output "aws_access_key_secret" {
  value = aws_iam_access_key.key.secret
  sensitive = true
}