from dataclasses import dataclass
from enum import Enum
import json
from typing import List
import boto3
from dataclass_wizard import JSONWizard


@dataclass
class SageMakerResources(JSONWizard):
    sagemaker_role_arn: str
    bucket_public: str
    domain_id: str


@dataclass
class BuildResources(JSONWizard):
    collegium_ecr: str


@dataclass
class AppResources:
    ses_source: str


class SSMParameter(Enum):
    # Shared resources that are not stack-specific.
    # Created by the admin. 
    APP_RESOURCES = "/collegium/app-resources"

    # Description of the team to be created by the Team stack.
    # Created by the admin.
    TEAM_CONFIG = "/collegium/team-config"

    # Created by the SageMaker stack.
    SAGEMAKER_RESOURCES = '/collegium/sagemaker-resources'

    # Created by the Build stack.
    BUILD_RESOURCES = '/collegium/build-resources'


@dataclass
class Member:
    name: str
    email: str


@dataclass
class TeamConfig(JSONWizard):
    admin: Member
    users: List[Member]


def load_build_resources() -> BuildResources:
    ssm = boto3.client('ssm', region_name='us-west-2')
    r = BuildResources.from_dict(json.loads(ssm.get_parameter(Name=SSMParameter.BUILD_RESOURCES.value)['Parameter']['Value']))
    return r

def load_sagemaker_resources() -> SageMakerResources:
    ssm = boto3.client('ssm', region_name='us-west-2')
    sagemaker_resources = SageMakerResources.from_dict(json.loads(ssm.get_parameter(Name=SSMParameter.SAGEMAKER_RESOURCES.value)['Parameter']['Value']))
    return sagemaker_resources


def load_team_config() -> TeamConfig:
    ssm = boto3.client('ssm', region_name='us-west-2')
    team_config = TeamConfig.from_dict(json.loads(ssm.get_parameter(Name=SSMParameter.TEAM_CONFIG.value)['Parameter']['Value']))
    return team_config