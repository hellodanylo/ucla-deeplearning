import base64
from pathlib import Path
from aws_cdk import RemovalPolicy, Stack
from aws_cdk import aws_sagemaker as sm
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_iam as iam
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ssm as ssm
from aws_cdk import aws_s3 as s3
from constructs import Construct
from collegium.cdk.environment import SSMParameter, SageMakerResources


class ImageConstruct(Construct):
    def __init__(self, scope: Construct, id: str, image_name: str, image_uri: str, role: iam.Role) -> None:
        super().__init__(scope, id)

        self.image = sm.CfnImage(
            self,
            f'Image',
            image_name=image_name,
            image_role_arn=role.role_arn
        )

        self.image_version = sm.CfnImageVersion(
            self, f'ImageVersion', 
            base_image=image_uri,
            image_name=image_name
        )
        self.image_version.apply_removal_policy(RemovalPolicy.RETAIN)

        self.image_version.add_dependency(self.image)

        self.app_image = sm.CfnAppImageConfig(
            self, f'AppImageConfig', 
            app_image_config_name=f'{image_name}-r2',
            jupyter_lab_app_image_config=sm.CfnAppImageConfig.JupyterLabAppImageConfigProperty(),
        )


class SageMakerStack(Stack):
    def __init__(self, scope: Construct, id: str, image_version: str):
        super().__init__(scope, id)

        role: iam.Role = iam.Role(
            self, 'SageMakerRole', 
            assumed_by=iam.ServicePrincipal('sagemaker.amazonaws.com'), 
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSageMakerFullAccess'),
                iam.ManagedPolicy.from_aws_managed_policy_name('AWSCodeCommitReadOnly'),
                iam.ManagedPolicy.from_aws_managed_policy_name('AmazonS3FullAccess'),
                iam.ManagedPolicy.from_aws_managed_policy_name('AmazonRekognitionReadOnlyAccess'),
            ]
        )

        ecr_collegium = ecr.Repository.from_repository_name(self, 'CollegiumRepo', 'collegium')
        collegium_image = ImageConstruct(self, 'ImageCollegium', 'collegium', ecr_collegium.repository_uri_for_tag(image_version), role)

        vpc = ec2.Vpc(
            self, 'Collegium', 
            ip_addresses=ec2.IpAddresses.cidr('10.42.5.0/24'), max_azs=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(name='Private', subnet_type=ec2.SubnetType.PRIVATE_ISOLATED, cidr_mask=25),
                ec2.SubnetConfiguration(name='Public', subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=25),
            ],
        )

        sg = ec2.SecurityGroup(self, 'PublicSSH', vpc=vpc, security_group_name='collegium-devbox')
        sg.add_ingress_rule(ec2.Peer.ipv4('0.0.0.0/0'), ec2.Port.SSH)

        self.lifecycle_config = sm.CfnStudioLifecycleConfig(
            self, 'Lifecycle', 
            studio_lifecycle_config_app_type='JupyterLab', 
            studio_lifecycle_config_content=base64.b64encode((Path(__file__).parent / 'studio_jupyter_lifecycle.sh').read_bytes()).decode(),
            studio_lifecycle_config_name='collegium-r4'
        )
        self.lifecycle_config.apply_removal_policy(RemovalPolicy.RETAIN)

        self.domain: sm.CfnDomain = sm.CfnDomain(
            self, 'Domain', 
            domain_name='ucla-deeplearning',
            auth_mode='IAM',
            default_user_settings=sm.CfnDomain.UserSettingsProperty(
                execution_role=role.role_arn,
                studio_web_portal="ENABLED",
                studio_web_portal_settings=sm.CfnDomain.StudioWebPortalSettingsProperty(
                    hidden_app_types=['CodeEditor', 'Canvas', 'JupyterServer', 'RStudioServerPro'],
                    hidden_ml_tools=[
                        'Comet',
                        'DeepchecksLLMEvaluation',
                        'Fiddler',
                        'LakeraGuard',
                        'DataWrangler',
                        'FeatureStore',
                        'EmrClusters',
                        'AutoMl',
                        'Experiments',
                        'Training',
                        'ModelEvaluation',
                        'InferenceOptimization',
                        'PerformanceEvaluation',
                        'Pipelines',
                        'Models',
                        'JumpStart',
                        'InferenceRecommender',
                        'Endpoints',
                        'Projects',
                        'HyperPodClusters'
                    ],
                    hidden_instance_types=['ml.t3.medium', 'ml.t3.large', 'ml.t3.2xlarge', 'ml.g4dn.xlarge', 'ml.g4dn.2xlarge', 'ml.g4dn.8xlarge', 'ml.g4dn.12xlarge', 'ml.g4dn.16xlarge'],
                ),
                default_landing_uri='studio::',
                jupyter_lab_app_settings=sm.CfnDomain.JupyterLabAppSettingsProperty(
                    lifecycle_config_arns=[self.lifecycle_config.attr_studio_lifecycle_config_arn],
                    default_resource_spec=sm.CfnDomain.ResourceSpecProperty(
                        lifecycle_config_arn=self.lifecycle_config.attr_studio_lifecycle_config_arn,
                        sage_maker_image_version_arn=collegium_image.image_version.attr_image_version_arn,
                        instance_type='ml.t3.xlarge'
                    ),
                    custom_images=[sm.CfnDomain.CustomImageProperty(
                        app_image_config_name=collegium_image.app_image.app_image_config_name,
                        image_name=collegium_image.image.image_name,
                        image_version_number=collegium_image.image_version.attr_version
                    )]
                ),
            ),
            subnet_ids=vpc.select_subnets().subnet_ids,
            vpc_id=vpc.vpc_id,
        )


        # bucket = s3.Bucket(
        #     self, 'BucketPublic', 
        #     access_control=s3.BucketAccessControl.PUBLIC_READ, 
        #     bucket_name='ucla-deeplearning-public',
        #     public_read_access=True,
        #     block_public_access=s3.BlockPublicAccess(
        #         block_public_acls=False, 
        #         block_public_policy=False, 
        #         ignore_public_acls=False, 
        #         restrict_public_buckets=False
        #     )
        # )

        ssm.CfnParameter(
            self, 'SageMakerResources', 
            value=SageMakerResources(
                bucket_public='danylo-ucla',
                sagemaker_role_arn=role.role_arn,
                domain_id=self.domain.attr_domain_id,
            ).to_json(),
            name=SSMParameter.SAGEMAKER_RESOURCES.value,
            type='String'
        )
