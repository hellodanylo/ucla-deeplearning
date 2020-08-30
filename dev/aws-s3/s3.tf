resource "aws_s3_bucket" "private" {
  bucket = "${prefix}-ucla-deep-learning-private"
  acl = "private"
}

output "s3_private" {
  value = {
    name = aws_s3_bucket.private.bucket
  }
}