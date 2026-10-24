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


def get_studio_image_tag():
    # The Studio image is tagged by the git tree hash of cdk/docker-studio (same formula as cdk/build_main.sh),
    # so it only changes when the image's environment changes
    tag = os.environ.get('STUDIO_IMAGE_TAG')
    if tag:
        return tag
    tree = subprocess.check_output(['git', 'rev-parse', 'HEAD:cdk/docker-studio']).decode().strip()
    return f'env-{tree[:12]}'


def main():
    app = App()
    build = BuildStack(app, 'CollegiumBuild')
    sagemaker: SageMakerStack = SageMakerStack(app, 'CollegiumSageMaker', image_version=get_studio_image_tag())

    ssm = boto3.client('ssm', region_name='us-west-2')
    config_json = ssm.get_parameter(Name=SSMParameter.TEAM_CONFIG.value)['Parameter']['Value']
    team_config = TeamConfig.from_json(config_json)
    assert isinstance(team_config, TeamConfig)

    iam_team = TeamStack(app, 'CollegiumTeam', sagemaker.domain.attr_domain_id, team_config)

    app.synth()


if __name__ == '__main__':
    main()