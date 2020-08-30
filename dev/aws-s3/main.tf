variable "s3_bucket_name" {
  type = string
}

terraform {
  required_providers {
    aws = {
      version = "3.4.0"
    }
  }
}

provider "aws" {
  region  = "us-west-2"
  profile = "ucla"
}

resource "aws_s3_bucket" "private" {
  bucket = var.s3_bucket_name
  acl = "private"
}

output "s3_bucket_name" {
  value = aws_s3_bucket.private.bucket
}