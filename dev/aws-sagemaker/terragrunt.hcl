remote_state {
  backend = "s3"
  config  = {
    bucket         = dependency.s3.outputs.s3_bucket_name
    key            = "terraform/aws-sagemaker.tfstate"
    region         = dependency.s3.outputs.s3_bucket_region
    dynamodb_table = "ucla-deeplearning-terraform-lock"
    profile        = "ucla"
  }
}

dependency "s3" {
  config_path = "../aws-s3"
}