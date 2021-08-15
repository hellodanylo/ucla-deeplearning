terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "3.53.0"
    }
  }

  backend "s3" {}
}

variable "members" {
  type = set(object({
    name = string
    email = string
  }))
}

variable "team" {
  type = object({
    admin_email = string
  })
}

module "users" {
  source = "../aws-budget"
  member = each.value
  team = var.team
  for_each = { for inst in var.members : inst.name => inst }
}