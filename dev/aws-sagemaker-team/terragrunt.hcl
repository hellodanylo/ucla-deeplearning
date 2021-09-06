remote_state {
  backend = "s3"
  config  = {
    bucket         = dependency.s3.outputs.s3_bucket_name
    key            = "terraform/aws-sagemaker-team.tfstate"
    region         = dependency.s3.outputs.s3_bucket_region
    dynamodb_table = "ucla-deeplearning-terraform-lock"
  }
}

dependency "s3" {
  config_path = "../aws-s3"
}

dependency "sagemaker" {
  config_path = "../aws-sagemaker"
}

inputs = {
  instance_type="ml.t3.xlarge"
  volume_size_gb=100
  sagemaker_config=dependency.sagemaker.outputs
  members = csvdecode(file("${path_relative_to_include()}/../members.csv"))
}
