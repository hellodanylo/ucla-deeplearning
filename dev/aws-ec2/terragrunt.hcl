remote_state {
  backend = "s3"
  config  = {
    bucket         = get_env("s3_bucket_name")
    key            = "terraform/aws-ec2.tfstate"
    region         = get_env("AWS_REGION")
    dynamodb_table = "ucla-deeplearning-terraform-lock"
  }
}

inputs = {
  region = get_env("AWS_REGION")
}