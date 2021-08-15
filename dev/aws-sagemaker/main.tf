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

locals {
  conda_lock_yml = file("${path.module}/../docker-jupyter/conda_lock.yml")

  notebook_on_create = templatefile("${path.module}/notebook_on_create.sh", {
    conda_lock_yml = local.conda_lock_yml
  })

  notebook_on_start = file("${path.module}/notebook_on_start.sh")
}

resource "aws_sagemaker_notebook_instance_lifecycle_configuration" "ucla_deeplearning" {
  name      = "ucla-deeplearning-notebook"
  on_create = base64encode(local.notebook_on_create)
  on_start = base64encode(local.notebook_on_start)
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

output "dynamodb_table_name" {
  value = aws_dynamodb_table.table.name
}

output "code_repository_name" {
  value = aws_sagemaker_code_repository.repo.code_repository_name
}

output "lifecycle_config_name" {
  value = aws_sagemaker_notebook_instance_lifecycle_configuration.ucla_deeplearning.name
}