terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "4.30.0"
    }
  }
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

variable "sns_topic_arn" {
  type = string
}

locals {
  full_thresholds = [0, 25, 50, 75, 90, 100]
  daily_thresholds = [0, 25, 50, 75, 100]
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
      format("%s$%s", "user:owner", var.member.name)
    ]
  }

  dynamic "notification" {
    for_each = local.full_thresholds
    content {
      comparison_operator = "GREATER_THAN"
      threshold = notification.value
      threshold_type = "PERCENTAGE"
      notification_type = "ACTUAL"
      subscriber_email_addresses = [
        var.team.admin_email,
        var.member.email
      ]
      subscriber_sns_topic_arns = (
        notification.value == 100
          ? [var.sns_topic_arn]
          : []
        )
    }
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
      format("%s$%s", "user:owner", var.member.name)
    ]
  }

  dynamic "notification" {
    for_each = local.daily_thresholds
    content {
      comparison_operator = "GREATER_THAN"
      threshold = notification.value
      threshold_type = "PERCENTAGE"
      notification_type = "ACTUAL"
      subscriber_email_addresses = [
        var.team.admin_email,
        var.member.email
      ]
      subscriber_sns_topic_arns = (
        notification.value == 100
          ? [var.sns_topic_arn]
          : []
      )
    }
  }
}