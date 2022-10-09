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
    admin_email = string
  })
}

variable "sns_topic_arn" {
  type = string
}

resource "aws_budgets_budget" "account_daily" {
  name = "account-daily"
  budget_type = "COST"
  limit_amount = "10"
  limit_unit = "USD"
  time_period_start = "2021-08-01_00:00"
  time_unit = "DAILY"

  dynamic "notification" {
    for_each = [0, 25, 50, 75, 100]
    content {
      comparison_operator = "GREATER_THAN"
      threshold = notification.value
      threshold_type = "PERCENTAGE"
      notification_type = "ACTUAL"
      subscriber_email_addresses = [
        var.team.admin_email,
      ]
      subscriber_sns_topic_arns = [
        var.sns_topic_arn]
    }
  }
}

resource "aws_budgets_budget" "account_annually" {
  name = "account-annually"
  budget_type = "COST"
  limit_amount = "2400"
  limit_unit = "USD"
  time_period_start = "2022-08-01_00:00"
  time_unit = "ANNUALLY"

  dynamic "notification" {
    for_each = [10, 20, 40, 50, 60, 70, 80, 90, 95, 100]
    content {
      comparison_operator = "GREATER_THAN"
      threshold = notification.value
      threshold_type = "PERCENTAGE"
      notification_type = "ACTUAL"
      subscriber_email_addresses = [
        var.team.admin_email,
      ]
      subscriber_sns_topic_arns = [
        var.sns_topic_arn]
    }
  }
}

module "users" {
  source = "../aws-budget"
  member = each.value
  team = var.team
  sns_topic_arn = var.sns_topic_arn
  for_each = { for inst in var.members : inst.name => inst }
}