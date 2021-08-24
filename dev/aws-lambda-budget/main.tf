terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "3.53.0"
    }
  }

  backend "s3" {}
}

resource "aws_sns_topic" "member_budget_alert" {
  name = "member-budget-alert"
  policy = file("${path.module}/topic_policy.json")
}

resource "aws_sns_topic_subscription" "member_budget_alert" {
  protocol = "lambda"
  topic_arn = aws_sns_topic.member_budget_alert.arn
  endpoint = aws_lambda_function.member_budget_alert.arn
}

data "archive_file" "lambda" {
  type        = "zip"
  source_file = "${path.module}/aws_lambda.py"
  output_path = "${path.module}/lambda.zip"
}

resource "aws_lambda_function" "member_budget_alert" {
  function_name = "ucla-deeplearning-member-budget-alert"
  filename = data.archive_file.lambda.output_path
  handler = "aws_lambda.handle"
  role = aws_iam_role.member_budget_alert.arn
  source_code_hash = filebase64sha256(data.archive_file.lambda.output_path)
  runtime = "python3.8"
  publish = "true"

  depends_on = [
    aws_iam_role_policy_attachment.member_budget_alert,
  ]
}

resource "aws_lambda_permission" "with_sns" {
  statement_id  = "AllowExecutionFromSNS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.member_budget_alert.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.member_budget_alert.arn
}

resource "aws_iam_role" "member_budget_alert" {
  name = "ucla-deeplearning-member-budget-alert"
  assume_role_policy = file("${path.module}/assume.json")
}

resource "aws_iam_policy" "member_budget_alert" {
  name = aws_iam_role.member_budget_alert.name
  path = "/"
  policy = file("${path.module}/policy.json")
}

resource "aws_iam_role_policy_attachment" "member_budget_alert" {
  role = aws_iam_role.member_budget_alert.name
  policy_arn = aws_iam_policy.member_budget_alert.arn
}

output "sns_topic_arn" {
  value = aws_sns_topic.member_budget_alert.id
}