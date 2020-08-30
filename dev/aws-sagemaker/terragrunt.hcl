remote_state {
  backend = "s3"
  config  = {
    profile        = "ucla"
    bucket         = get_env("s3_bucket_name")
    key            = "terraform/aws-sagemaker.tfstate"
    region         = "us-west-2"
    dynamodb_table = "ucla-deeplearning-terraform-lock"
  }
}