import csv
import os
from pathlib import Path
import subprocess
from aws_cdk import App
from build_stack import BuildStack
from environment import SSMParameter
from team_stack import TeamConfig, TeamStack, Member
from sagemaker_stack import SageMakerStack
import boto3


def get_current_version():
    version = os.environ.get('CODEBUILD_RESOLVED_SOURCE_VERSION')
    if version:
        return version
    version = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
    return version


def main():
    app = App()
    build = BuildStack(app, 'Build')
    version = get_current_version()

    sagemaker: SageMakerStack = SageMakerStack(app, 'SageMaker', image_version=version)

    ssm = boto3.client('ssm', region_name='us-west-2')
    config_json = ssm.get_parameter(Name=SSMParameter.TEAM_CONFIG.value)['Parameter']['Value']
    team_config = TeamConfig.from_json(config_json)
    assert isinstance(team_config, TeamConfig)

    iam_team = TeamStack(app, 'Team', sagemaker.domain.attr_domain_id, team_config)

    app.synth()


if __name__ == '__main__':
    main()