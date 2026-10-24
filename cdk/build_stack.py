from enum import Enum
import json
import os
import aws_cdk.aws_ecr as ecr
import aws_cdk.aws_codebuild as cb
import aws_cdk.aws_codecommit as cc
import aws_cdk.aws_codepipeline as cp
import aws_cdk.aws_codepipeline_actions as cpa
import aws_cdk.aws_iam as iam
import aws_cdk.aws_ssm as ssm
import aws_cdk.aws_sns as sns
from aws_cdk import Stack, Duration, RemovalPolicy
import boto3.session
from constructs import Construct
import boto3

from collegium.cdk.environment import BuildResources, SSMParameter


class BuildVariable(Enum):
    COLLEGIUM_ECR = "COLLEGIUM_ECR"
    COLLEGIUM_CDK_ECR = "COLLEGIUM_CDK_ECR"


class BuildStack(Stack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)
        package_name = "collegium"

        git_repo = cc.Repository(
            self, "CodeCommitRepository",
            repository_name=package_name,
        )

        # SageMaker Studio image (cdk/docker-studio)
        ecr_repo: ecr.Repository = ecr.Repository(
            self, "ECRRepository", 
            repository_name=package_name,
            lifecycle_rules=[
                ecr.LifecycleRule(
                    tag_status=ecr.TagStatus.ANY, 
                    max_image_age=Duration.days(90),
                    description="keep for 90 days"
                ),
            ],
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Deployment tooling image (cdk/docker-cdk)
        ecr_repo_cdk: ecr.Repository = ecr.Repository(
            self, "ECRRepositoryCdk",
            repository_name=f"{package_name}-cdk",
            lifecycle_rules=[
                ecr.LifecycleRule(
                    tag_status=ecr.TagStatus.ANY,
                    max_image_age=Duration.days(90),
                    description="keep for 90 days"
                ),
            ],
            removal_policy=RemovalPolicy.DESTROY,
        )

        role: iam.Role = iam.Role(
            self, "IamRoleBuild", 
            role_name=f"{package_name}-codebuild",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal(service="codepipeline.amazonaws.com"),
                iam.ServicePrincipal(service="codebuild.amazonaws.com"),
                # iam.ArnPrincipal(f"arn:aws:iam::{self.account}:role/{package_name}-codebuild"),
                iam.AccountPrincipal(self.account),
            ),
            managed_policies=[
                iam.ManagedPolicy.from_managed_policy_arn(self, arn, managed_policy_arn=arn)
                for arn in [
                    "arn:aws:iam::aws:policy/AdministratorAccess",
                ]
            ]
        )

        project = cb.PipelineProject(
            self, 
            f'CodeBuildProject', 
            project_name=package_name,
            environment=cb.BuildEnvironment(
                build_image=cb.LinuxBuildImage.STANDARD_7_0,
                compute_type=cb.ComputeType.MEDIUM,
                privileged=True
            ),
            role=role,  # type: ignore
            build_spec=cb.BuildSpec.from_source_filename("cdk/buildspec.yml"),
            timeout=Duration.hours(2),
        )

        ssm_client = boto3.client('ssm', region_name=os.environ.get('AWS_REGION'))
        app_resources = json.loads(ssm_client.get_parameter(Name=SSMParameter.APP_RESOURCES.value)['Parameter']['Value'])
        code_connection_arn = app_resources['code_connection_arn']
        source = cp.Artifact(artifact_name=package_name)

        pipeline: cp.Pipeline = cp.Pipeline(
            self, 'CodePipeline',
            pipeline_name=package_name,
            role=role,  # type: ignore
            stages=[
                cp.StageProps(stage_name="source", actions=[
                    cpa.CodeStarConnectionsSourceAction(
                        owner="hellodanylo",
                        repo="ucla-deeplearning",
                        connection_arn=code_connection_arn,
                        code_build_clone_output=True,
                        action_name=package_name,
                        output=source,
                        branch='main',
                        role=role,  # type: ignore
                    )
                ]),
                cp.StageProps(stage_name="deploy", actions=[
                    cpa.CodeBuildAction(
                        action_name=package_name, 
                        input=source, 
                        project=project,  # type: ignore
                        role=role,  # type: ignore
                        environment_variables={
                            BuildVariable.COLLEGIUM_ECR.value: cb.BuildEnvironmentVariable(value=ecr_repo.repository_uri),
                            BuildVariable.COLLEGIUM_CDK_ECR.value: cb.BuildEnvironmentVariable(value=ecr_repo_cdk.repository_uri),
                        }
                    ) 
                ]),
            ]
        )
        topic: sns.Topic = sns.Topic(self, 'Topic', display_name='collegium-build', topic_name='collegium-build')
        pipeline.notify_on(
            id="notify_success_or_failure",
            target=topic, 
            events=[cp.PipelineNotificationEvents.PIPELINE_EXECUTION_FAILED, cp.PipelineNotificationEvents.PIPELINE_EXECUTION_SUCCEEDED]
        )

        ssm.CfnParameter(
            self, 'BuildResources', 
            value=BuildResources(
                collegium_ecr=ecr_repo.repository_uri,
                collegium_cdk_ecr=ecr_repo_cdk.repository_uri,
            ).to_json(),
            name=SSMParameter.BUILD_RESOURCES.value,
            type='String'
        )
