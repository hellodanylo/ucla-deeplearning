terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "4.30.0"
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
    admin_account_id = string
  })
}

module "users" {
  source = "../aws-iam-user"
  team = var.team
  member = each.value
  for_each = { for inst in var.members : inst.name => inst }
}

output "users" {
  value = module.users
  sensitive = true
}