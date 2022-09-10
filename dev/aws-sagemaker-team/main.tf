terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "4.30.0"
    }
  }

  backend "s3" {}
}

variable "instance_type" {
  type = string
}
variable "volume_size_gb" {
  type = number
}

variable "sagemaker_config" {
  type = any
}

variable "members" {
  type = set(object({
    name = string
    email = string
  }))
}

module "notebooks" {
  source = "../aws-sagemaker-notebook"
  sagemaker_config = var.sagemaker_config
  instance_type = var.instance_type
  member_name = each.key
  notebook_name = "ucla-deeplearning-${each.key}"
  volume_size_gb = var.volume_size_gb

  for_each = { for inst in var.members : inst.name => inst }
}