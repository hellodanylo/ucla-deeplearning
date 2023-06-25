from aws_cdk import Stack
from aws_cdk import aws_sagemaker as sm
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_iam as iam
from aws_cdk import aws_ec2 as ec2
from constructs import Construct


class ImageConstruct(Construct):
    def __init__(self, scope: Construct, id: str, repo: ecr.Repository, role: iam.Role, flavor: str) -> None:
        super().__init__(scope, id)

        self.image = sm.CfnImage(
            self,
            f'Image',
            image_name=f'doctrina-{flavor}',
            image_role_arn=role.role_arn
        )

        self.image_version = sm.CfnImageVersion(
            self, f'ImageVersion', 
            base_image=repo.repository_uri_for_tag(f'{flavor}-latest'),
            image_name=f'doctrina-{flavor}'
        )

        self.image_version.add_dependency(self.image)

        self.app_image = sm.CfnAppImageConfig(
            self, f'AppImageConfig', 
            app_image_config_name=self.image_version.image_name,
            kernel_gateway_image_config=sm.CfnAppImageConfig.KernelGatewayImageConfigProperty(
                kernel_specs=[
                    sm.CfnAppImageConfig.KernelSpecProperty(name='python3', display_name=f'doctrina-{flavor}')
                ]
            ),
        )


class SageMakerStack(Stack):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        role = iam.Role(
            self, 'SageMakerRole', 
            assumed_by=iam.ServicePrincipal('sagemaker.amazonaws.com'), 
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSageMakerFullAccess'),
                iam.ManagedPolicy.from_aws_managed_policy_name('AWSCodeCommitReadOnly'),
            ]
        )

        repo = ecr.Repository.from_repository_name(self, 'DoctrinaRepo', 'doctrina')
        images = [
            ImageConstruct(self, f'Image{flavor.capitalize()}', repo=repo, role=role, flavor=flavor)
            for flavor in ['torch', 'tf2']
        ]

        vpc = ec2.Vpc(
            self, 'Collegium', 
            ip_addresses=ec2.IpAddresses.cidr('10.42.5.0/24'), max_azs=1,
            subnet_configuration=[ec2.SubnetConfiguration(name='Private', subnet_type=ec2.SubnetType.PRIVATE_ISOLATED, cidr_mask=25)],
        )

        domain = sm.CfnDomain(
            self, 'Domain', 
            domain_name='ucla-deeplearning',
            auth_mode='IAM',
            default_user_settings=sm.CfnDomain.UserSettingsProperty(
                execution_role=role.role_arn,
                kernel_gateway_app_settings=sm.CfnDomain.KernelGatewayAppSettingsProperty(
                    custom_images=[
                        sm.CfnDomain.CustomImageProperty(
                            app_image_config_name=image.app_image.app_image_config_name,
                            image_name=image.image.image_name,
                            image_version_number=image.image_version.attr_version,
                        )
                        for image in images
                    ]
                )
            ),
            subnet_ids=vpc.select_subnets().subnet_ids,
            vpc_id=vpc.vpc_id,
            
        )

        user = sm.CfnUserProfile(
            self, 'DomainUser', 
            domain_id=domain.attr_domain_id, 
            user_profile_name='admin'
        )
