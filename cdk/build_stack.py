from enum import Enum
import aws_cdk.aws_ecr as ecr
import aws_cdk.aws_codebuild as cb
import aws_cdk.aws_codecommit as cc
import aws_cdk.aws_codepipeline as cp
import aws_cdk.aws_codepipeline_actions as cpa
import aws_cdk.aws_iam as iam
import aws_cdk.aws_events as e
import aws_cdk.aws_events_targets as et
from aws_cdk import Stack, Duration


class BuildStage(Enum):
    DOCKER = "docker"
    TEST = "test"
    CDK = "cdk"


class BuildVariable(Enum):
    BUILD_STAGE = "BUILD_STAGE"
    COLLEGIUM_ECR = "COLLEGIUM_ECR"
    DOCTRINA_ECR = "DOCTRINA_ECR"


class BuildStack(Stack):
    def __init__(self, 
        *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        package_name = "collegium"

        git_repo = cc.Repository(
            self, "CodeCommitRepository",
            repository_name=package_name,
        )

        ecr_repo = ecr.Repository(
            self, "ECRRepository", 
            repository_name=package_name,
            lifecycle_rules=[
                ecr.LifecycleRule(
                    tag_status=ecr.TagStatus.ANY, 
                    max_image_count=5,
                    description="keep last 5 images"
                ),
            ]
        )

        ecr_doctrina = ecr.Repository.from_repository_name(self, "ECRRepositoryHumus", repository_name="doctrina")

        role = iam.Role(
            self, "IamRoleBuild", 
            role_name=f"{package_name}-codebuild",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal(service="codepipeline.amazonaws.com"),
                iam.ServicePrincipal(service="codebuild.amazonaws.com"),
            ),
            managed_policies=[
                iam.ManagedPolicy.from_managed_policy_arn(self, arn, managed_policy_arn=arn)
                for arn in [
                    "arn:aws:iam::aws:policy/AWSCloudFormationFullAccess",
                    "arn:aws:iam::aws:policy/AWSCodeBuildAdminAccess",
                    "arn:aws:iam::aws:policy/AWSCodeCommitPowerUser",
                    "arn:aws:iam::aws:policy/AWSCodePipeline_FullAccess",
                    "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess",
                    "arn:aws:iam::aws:policy/AmazonEC2FullAccess",
                    "arn:aws:iam::aws:policy/AmazonS3FullAccess",
                    "arn:aws:iam::aws:policy/AmazonSSMFullAccess",
                    "arn:aws:iam::aws:policy/CloudWatchFullAccess",
                    "arn:aws:iam::aws:policy/IAMFullAccess",
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
            build_spec=cb.BuildSpec.from_source_filename("cdk/buildspec.yml")
        )

        source = cp.Artifact(artifact_name=package_name)

        pipeline = cp.Pipeline(
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
                cp.StageProps(stage_name=BuildStage.DOCKER.value, actions=[
                    cpa.CodeBuildAction(
                        action_name=package_name, 
                        input=source, 
                        project=project,  # type: ignore
                        role=role,  # type: ignore
                        environment_variables={
                            BuildVariable.BUILD_STAGE.value: cb.BuildEnvironmentVariable(value=BuildStage.DOCKER.value, type=cb.BuildEnvironmentVariableType.PLAINTEXT),
                            BuildVariable.DOCTRINA_ECR.value: cb.BuildEnvironmentVariable(value=ecr_doctrina.repository_uri, type=cb.BuildEnvironmentVariableType.PLAINTEXT),
                            BuildVariable.COLLEGIUM_ECR.value: cb.BuildEnvironmentVariable(value=ecr_repo.repository_uri),
                        }
                    ) 
                ]),
                # cp.StageProps(stage_name=BuildStage.TEST.value, actions=[
                #     cpa.CodeBuildAction(
                #         action_name=package_name, 
                #         input=source, 
                #         project=project,  # type: ignore
                #         role=role,  # type: ignore
                #         environment_variables={
                #             BuildVariable.BUILD_STAGE.value: cb.BuildEnvironmentVariable(value=BuildStage.TEST.value, type=cb.BuildEnvironmentVariableType.PLAINTEXT),
                #             BuildVariable.COLLEGIUM_ECR.value: cb.BuildEnvironmentVariable(value=ecr_repo.repository_uri),
                #         }
                #     ) 
                # ]),
                cp.StageProps(stage_name=BuildStage.CDK.value, actions=[
                    cpa.CodeBuildAction(
                        action_name=package_name, 
                        input=source, 
                        project=project,  # type: ignore
                        role=role,  # type: ignore
                        environment_variables={
                            BuildVariable.BUILD_STAGE.value: cb.BuildEnvironmentVariable(value=BuildStage.CDK.value, type=cb.BuildEnvironmentVariableType.PLAINTEXT),
                            BuildVariable.COLLEGIUM_ECR.value: cb.BuildEnvironmentVariable(value=ecr_repo.repository_uri),
                        }
                    ) 
                ]),
            ]
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
                    "repository-name": [ecr_doctrina.repository_name]
                }
            ),
            targets=[et.CodePipeline(
                pipeline=pipeline, 
                event_role=event_role  # type: ignore
            )]
        )