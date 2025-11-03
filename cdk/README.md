# Deployment Steps
1. create SSM parameters `/collegium/team-config` and `/collegium/image-environment`
2. deploy `CollegiumBuild` via local repo
3. push `collegium` to CodeCommit
4. wait for CodePipeline to finish: image build, test, cdk deploy
5. attach lifecycle policy to the SageMaker domain

# Maintenance Steps
If the Studio lifecycle script has changed, it must be recreated by changing the CDK resource name.

# Cleanup Steps
1. delete all SageMaker apps
2. delete EFS volume
3. delete EFS-related security groups
4. delete EC2 instances in the SageMaker VPC
4. delete `CollegiumTeam` stack
5. delete `CollegiumSageMaker` stack
6. delete `CollegiumBuild` stack
7. delete CodePipeline's artifact S3 bucket
8. delete SSM parameters
9. delete SageMaker images and lifecycle configurations
