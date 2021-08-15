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
    admin_email = string
  })
}

resource "aws_budgets_budget" "full" {
  name = "${var.member.name}-full"
  budget_type = "COST"
  limit_amount = "100"
  limit_unit = "USD"
  time_period_start = "2021-08-01_00:00"
  time_unit = "ANNUALLY"
  cost_filter {
    name = "TagKeyValue"
    values = [
      "Member$${var.member.name}"
    ]
  }

  notification {
    comparison_operator = "GREATER_THAN"
    threshold = 0
    threshold_type = "PERCENTAGE"
    notification_type = "ACTUAL"
    subscriber_email_addresses = [
      var.team.admin_email,
      var.member.email
    ]
  }

  notification {
    comparison_operator = "GREATER_THAN"
    threshold = 50
    threshold_type = "PERCENTAGE"
    notification_type = "ACTUAL"
    subscriber_email_addresses = [
      var.team.admin_email,
      var.member.email
    ]
  }

  notification {
    comparison_operator = "GREATER_THAN"
    threshold = 75
    threshold_type = "PERCENTAGE"
    notification_type = "ACTUAL"
    subscriber_email_addresses = [
      var.team.admin_email,
      var.member.email
    ]
  }

  notification {
    comparison_operator = "GREATER_THAN"
    threshold = 100
    threshold_type = "PERCENTAGE"
    notification_type = "ACTUAL"
    subscriber_email_addresses = [
      var.team.admin_email,
      var.member.email
    ]
  }
}
resource "aws_budgets_budget" "daily" {
  name = "${var.member.name}-daily"
  budget_type = "COST"
  limit_amount = "10"
  limit_unit = "USD"
  time_period_start = "2021-08-01_00:00"
  time_unit = "DAILY"
  cost_filter {
    name = "TagKeyValue"
    values = [
      "Member$${var.member.name}"
    ]
  }

  notification {
    comparison_operator = "GREATER_THAN"
    threshold = 50
    threshold_type = "PERCENTAGE"
    notification_type = "ACTUAL"
    subscriber_email_addresses = [
      var.team.admin_email,
      var.member.email
    ]
  }

  notification {
    comparison_operator = "GREATER_THAN"
    threshold = 100
    threshold_type = "PERCENTAGE"
    notification_type = "ACTUAL"
    subscriber_email_addresses = [
      var.team.admin_email,
      var.member.email
    ]
  }
}