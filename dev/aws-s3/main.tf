terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "4.30.0"
    }
  }
}

variable "s3_bucket_name" {
  type = string
}

data "aws_region" "current" {}

resource "aws_kms_key" "s3_key" {
  description = "Encryption key for ${var.s3_bucket_name}"
  deletion_window_in_days = 10
}

resource "aws_s3_bucket" "private" {
  bucket = var.s3_bucket_name
}

resource "aws_s3_bucket_acl" "private_acl" {
  bucket = aws_s3_bucket.private.id
  acl    = "private"
}

resource "aws_s3_bucket_versioning" "private_versioning" {
  bucket = aws_s3_bucket.private.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "private_encryption" {
  bucket = aws_s3_bucket.private.id

  rule {
    bucket_key_enabled = true
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
      kms_master_key_id = aws_kms_key.s3_key.arn
    }
  }
}

resource "aws_s3_bucket_public_access_block" "private" {
  bucket = aws_s3_bucket.private.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

output "s3_bucket_name" {
  value = aws_s3_bucket.private.bucket
}

output "s3_bucket_region" {
  value = data.aws_region.current.name
}