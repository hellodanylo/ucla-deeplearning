terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "3.4.0"
    }
  }
}

variable "s3_bucket_name" {
  type = string
}

data "aws_region" "current" {}

resource "aws_s3_bucket" "private" {
  bucket = var.s3_bucket_name
  acl = "private"
}

output "s3_bucket_name" {
  value = aws_s3_bucket.private.bucket
}

output "s3_bucket_region" {
  value = data.aws_region.current.name
}