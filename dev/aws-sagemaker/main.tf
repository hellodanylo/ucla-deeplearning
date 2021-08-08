terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "3.53.0"
    }
  }

  backend "s3" {}
}

data "aws_region" "current" {}

resource "aws_default_vpc" "default" {}

resource "aws_default_subnet" "default_az1" {
  availability_zone = "${data.aws_region.current.name}a"
}

resource "aws_iam_role" "sagemaker" {
  name               = "sagemaker_execution_role"
  assume_role_policy = file("${path.module}/sagemaker_assume_role.json")
}

resource "aws_iam_role_policy_attachment" "sagemaker_admin" {
  role       = aws_iam_role.sagemaker.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

resource "aws_security_group" "sagemaker" {
  name = "sagemaker-notebook"

  ingress {
    protocol  = -1
    self      = true
    from_port = 0
    to_port   = 0
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [
      "0.0.0.0/0"]
  }
}


resource "aws_sagemaker_code_repository" "repo" {
  code_repository_name = "ucla-deeplearning"

  git_config {
    repository_url = "https://github.com/hellodanylo/ucla-deeplearning.git"
  }
}

resource "aws_dynamodb_table" "table" {
  name = "ucla-deep-learning-notebooks"
  billing_mode = "PAY_PER_REQUEST"
  attribute {
    name = "name"
    type = "S"
  }
  hash_key = "name"
}

output "subnet_id" {
  value = aws_default_subnet.default_az1.id
}

output "security_group_id" {
  value = aws_security_group.sagemaker.id
}

output "role_arn" {
  value = aws_iam_role.sagemaker.arn
}

output "dynamodb_table_name" {
  value = aws_dynamodb_table.table.name
}

output "code_repository_name" {
  value = aws_sagemaker_code_repository.repo.code_repository_name
}