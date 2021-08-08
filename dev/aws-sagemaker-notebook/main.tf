terraform {
  required_providers {
    aws = {
      version = "3.53.0"
    }
  }

  backend "s3" {}
}

variable "notebook_name" {
  type = string
}

variable "subnet_id" {
  type = string
}

variable "security_group_id" {
  type = string
}

variable "role_arn" {
  type = string
}

variable "instance_type" {
  type = string
}

variable "code_repository_name" {
  type = string
}

variable "volume_size_gb" {
  type = number
}

locals {
  conda_lock_yml = file("${path.module}/../docker-jupyter/conda_lock.yml")

  notebook_on_create = templatefile("${path.module}/notebook_on_create.sh", {
    conda_lock_yml = local.conda_lock_yml
    sagemaker_notebook_name = var.notebook_name
  })

  notebook_on_start = file("${path.module}/notebook_on_start.sh")
}

resource "aws_sagemaker_notebook_instance_lifecycle_configuration" "ucla_deeplearning" {
  name      = var.notebook_name
  on_create = base64encode(local.notebook_on_create)
  on_start = base64encode(local.notebook_on_start)
}

resource "aws_sagemaker_notebook_instance" "notebook" {
  name          = var.notebook_name
  role_arn      = var.role_arn
  instance_type = var.instance_type
  default_code_repository = var.code_repository_name
  volume_size = var.volume_size_gb
  subnet_id = var.subnet_id
  security_groups = [var.security_group_id]
  lifecycle_config_name = aws_sagemaker_notebook_instance_lifecycle_configuration.ucla_deeplearning.name

  tags = {
    Name = "test"
  }
}

output "notebook_name" {
  value = var.notebook_name
}

output "volume_size_gb" {
  value = var.volume_size_gb
}