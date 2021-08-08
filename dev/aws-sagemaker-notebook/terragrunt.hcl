remote_state {
  backend = "s3"
  config  = {
    bucket         = dependency.s3.outputs.s3_bucket_name
    key            = "terraform/aws-sagemaker-notebook.tfstate"
    region         = dependency.s3.outputs.s3_bucket_region
    dynamodb_table = "ucla-deeplearning-terraform-lock"
    profile        = "ucla"
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
  subnet_id=dependency.sagemaker.outputs.subnet_id
  security_group_id=dependency.sagemaker.outputs.security_group_id
  role_arn=dependency.sagemaker.outputs.role_arn
  code_repository_name=dependency.sagemaker.outputs.code_repository_name
  volume_size_gb=20
}