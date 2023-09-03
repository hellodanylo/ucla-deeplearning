from enum import Enum
import aws_cdk.aws_ecr as ecr
import aws_cdk.aws_codebuild as cb
import aws_cdk.aws_codecommit as cc
import aws_cdk.aws_codepipeline as cp
import aws_cdk.aws_codepipeline_actions as cpa
import aws_cdk.aws_iam as iam
import aws_cdk.aws_events as e
import aws_cdk.aws_events_targets as et
import aws_cdk.aws_ssm as ssm
import aws_cdk.aws_codestarnotifications as csn
import aws_cdk.aws_sns as sns
import aws_cdk.aws_sns_subscriptions as sns_subs
from aws_cdk import Stack, Duration, RemovalPolicy
from constructs import Construct

from collegium.cdk.environment import BuildResources, SSMParameter


class BuildVariable(Enum):
    COLLEGIUM_ECR = "COLLEGIUM_ECR"
    DOCTRINA_ECR = "DOCTRINA_ECR"


class BuildStack(Stack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)
        package_name = "collegium"

        git_repo = cc.Repository(
            self, "CodeCommitRepository",
            repository_name=package_name,
        )

        ecr_repo: ecr.Repository = ecr.Repository(
            self, "ECRRepository", 
            repository_name=package_name,
            lifecycle_rules=[
                ecr.LifecycleRule(
                    tag_status=ecr.TagStatus.ANY, 
                    max_image_count=5,
                    description="keep last 5 images"
                ),
            ],
            removal_policy=RemovalPolicy.DESTROY,
        )

        ecr_doctrina = ecr.Repository.from_repository_name(self, "ECRRepositoryDoctrina", repository_name="doctrina")

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

        source = cp.Artifact(artifact_name=package_name)

        pipeline: cp.Pipeline = cp.Pipeline(
            self, 'CodePipeline',
            pipeline_name=package_name,
            role=role,  # type: ignore
            stages=[
                cp.StageProps(stage_name="source", actions=[
                    cpa.CodeCommitSourceAction(
                        repository=git_repo,
                        code_build_clone_output=True,
                        action_name=package_name,
                        output=source,
                        branch='main',
                        trigger=cpa.CodeCommitTrigger.EVENTS,
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
                            BuildVariable.DOCTRINA_ECR.value: cb.BuildEnvironmentVariable(value=ecr_doctrina.repository_uri, type=cb.BuildEnvironmentVariableType.PLAINTEXT),
                            BuildVariable.COLLEGIUM_ECR.value: cb.BuildEnvironmentVariable(value=ecr_repo.repository_uri),
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

        event_role = iam.Role(
            self, "RoleEvent", 
            role_name=f"{package_name}-event",
            assumed_by=iam.ServicePrincipal("events.amazonaws.com")
        )

        e.Rule(
            self, "EventRuleDoctrina", 
            rule_name=f"doctrina-ecr-trigger-{package_name}-build",
            event_pattern=e.EventPattern(
                source=["aws.ecr"],
                detail_type=["ECR Image Action"],
                detail={
                    "action-type": ["PUSH"],
                    "result": ["SUCCESS"],
                    "repository-name": [ecr_doctrina.repository_name],
                    "image-tag": ["base-latest"],
                }
            ),
            targets=[et.CodePipeline(
                pipeline=pipeline, 
                event_role=event_role  # type: ignore
            )]
        )

        ssm.CfnParameter(
            self, 'BuildResources', 
            value=BuildResources(
                collegium_ecr=ecr_repo.repository_uri
            ).to_json(),
            name=SSMParameter.BUILD_RESOURCES.value,
            type='String'
        )
