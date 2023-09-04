import base64
import json
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
from collegium.cdk.studio_lifecycle_construct import StudioLifeCycleConstruct, StudioLifeCycleProvider


class ImageConstruct(Construct):
    def __init__(self, scope: Construct, id: str, image_name: str, image_uri: str, role: iam.Role, kernel_name: str) -> None:
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
            app_image_config_name=self.image_version.image_name,
            kernel_gateway_image_config=sm.CfnAppImageConfig.KernelGatewayImageConfigProperty(
                kernel_specs=[
                    sm.CfnAppImageConfig.KernelSpecProperty(name=kernel_name, display_name=kernel_name)
                ]
            ),
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
        collegium_image = ImageConstruct(self, 'ImageCollegium', 'collegium', ecr_collegium.repository_uri_for_tag(image_version), role, "collegium")
        images = [collegium_image]

        vpc = ec2.Vpc(
            self, 'Collegium', 
            ip_addresses=ec2.IpAddresses.cidr('10.42.5.0/24'), max_azs=1,
            subnet_configuration=[ec2.SubnetConfiguration(name='Private', subnet_type=ec2.SubnetType.PRIVATE_ISOLATED, cidr_mask=25)],
        )

        lifecycle_provider = StudioLifeCycleProvider(self, "StudioLifecycleProvider")
    
        revision = '11'
        studio_jupyter_lifecycle = (Path(__file__).parent / 'studio_jupyter_lifecycle.sh').read_text().replace('{revision}', revision)
        studio_jupyter_lifecycle = base64.standard_b64encode(studio_jupyter_lifecycle.encode()).decode()
        jupyter_lifecycle = StudioLifeCycleConstruct(
            self, 'StudioJupyterLifecycle', 
            lifecycle_provider, 
            studio_jupyter_lifecycle, 'JupyterServer', f'collegium-jupyter-r{revision}'
        )

        revision = '3'
        studio_kernel_lifecycle = (Path(__file__).parent / 'studio_kernel_lifecycle.sh').read_text().replace('{revision}', revision)
        studio_kernel_lifecycle = base64.standard_b64encode(studio_kernel_lifecycle.encode()).decode()
        kernel_lifecycle = StudioLifeCycleConstruct(
            self, 'StudioKernelLifecycle', 
            lifecycle_provider, 
            studio_kernel_lifecycle, 'KernelGateway', f'collegium-kernel-r{revision}'
        )

        self.domain: sm.CfnDomain = sm.CfnDomain(
            self, 'Domain', 
            domain_name='ucla-deeplearning',
            auth_mode='IAM',
            default_user_settings=sm.CfnDomain.UserSettingsProperty(
                execution_role=role.role_arn,
                jupyter_server_app_settings=sm.CfnDomain.JupyterServerAppSettingsProperty(default_resource_spec=sm.CfnDomain.ResourceSpecProperty(
                    lifecycle_config_arn=jupyter_lifecycle.studio_lifecycle_config_arn,
                )),
                kernel_gateway_app_settings=sm.CfnDomain.KernelGatewayAppSettingsProperty(
                    default_resource_spec=sm.CfnDomain.ResourceSpecProperty(
                        instance_type="ml.t3.xlarge",
                        lifecycle_config_arn=kernel_lifecycle.studio_lifecycle_config_arn,
                        sage_maker_image_arn=collegium_image.image.attr_image_arn,
                        sage_maker_image_version_arn=collegium_image.image_version.attr_image_version_arn,
                    ),
                    # Disabled, because it detaches previous versions of images,
                    # that might still be in use by active profiles.
                    # custom_images=[
                    #     sm.CfnDomain.CustomImageProperty(
                    #         app_image_config_name=image.app_image.app_image_config_name,
                    #         image_name=image.image.image_name,
                    #         image_version_number=image.image_version.attr_version,
                    #     )
                    #     for image in images
                    # ]
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
            ).to_json(),
            name=SSMParameter.SAGEMAKER_RESOURCES.value,
            type='String'
        )
