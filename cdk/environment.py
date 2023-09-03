from dataclasses import dataclass
from enum import Enum

from dataclass_wizard import JSONWizard

@dataclass
class SageMakerResources(JSONWizard):
    sagemaker_role_arn: str
    bucket_public: str


@dataclass
class BuildResources(JSONWizard):
    collegium_ecr: str


class SSMParameter(Enum):
    # Description of the team to be created by the Team stack.
    # Created by the admin.
    TEAM_CONFIG = "/collegium/team-config"

    # Created by the SageMaker stack.
    SAGEMAKER_RESOURCES = '/collegium/sagemaker-resources'

    # Created by the Build stack.
    BUILD_RESOURCES = '/collegium/build-resources'