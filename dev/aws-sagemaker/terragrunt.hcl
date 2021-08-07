remote_state {
  backend = "s3"
  config  = {
    bucket         = get_env("s3_bucket_name")
    key            = "terraform/aws-sagemaker.tfstate"
    region         = get_env("s3_bucket_region")
    dynamodb_table = "ucla-deeplearning-terraform-lock"
    profile        = "ucla"
  }
}
