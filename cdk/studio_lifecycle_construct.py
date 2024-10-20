from pathlib import Path
from constructs import Construct
from aws_cdk import (
    aws_iam as iam,
    Duration,
    custom_resources,
    CustomResource,
    aws_lambda as l,
    RemovalPolicy
)


class StudioLifeCycleProvider(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str, 
    ):
        super().__init__(scope, id)
        lifecycle_config_role = iam.Role(
            self,
            "Role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSageMakerFullAccess'),
            ],
        )

        create_lifecycle_script_lambda = l.Function(
            self,
            "CreateLifeCycleConfigLambda",
            runtime=l.Runtime.PYTHON_3_8,
            timeout=Duration.minutes(3),
            code=l.Code.from_inline((Path(__file__).parent / 'studio_lifecycle_lambda.py').read_text()),
            handler="index.handler",
            role=lifecycle_config_role,  # type: ignore
        )

        self.provider = custom_resources.Provider(
            self,
            "ResourceProvider",
            on_event_handler=create_lifecycle_script_lambda,  # type: ignore
        )


class StudioLifeCycleConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        provider: StudioLifeCycleProvider,
        studio_lifecycle_config_content: str,
        studio_lifecycle_config_app_type: str,
        studio_lifecycle_config_name: str,
    ):
        super().__init__(scope, id)
        self.studio_lifecycle_config_content = studio_lifecycle_config_content
        self.studio_lifecycle_config_name = studio_lifecycle_config_name
        self.studio_lifecycle_config_app_type = studio_lifecycle_config_app_type

        studio_lifecycle_config_custom_resource: CustomResource = CustomResource(
            self,
            id=studio_lifecycle_config_name,
            service_token=provider.provider.service_token,
            properties={
                "studio_lifecycle_config_content": self.studio_lifecycle_config_content,
                "studio_lifecycle_config_name": self.studio_lifecycle_config_name,
                "studio_lifecycle_config_app_type": self.studio_lifecycle_config_app_type,
            },
            removal_policy=RemovalPolicy.RETAIN_ON_UPDATE_OR_DELETE,
        )
        self.studio_lifecycle_config_arn = (
            studio_lifecycle_config_custom_resource.get_att_string("StudioLifecycleConfigArn")
        )