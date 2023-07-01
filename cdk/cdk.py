import csv
import os
from pathlib import Path
import subprocess
from aws_cdk import App
from build_stack import BuildStack
from team_stack import TeamStack, Member
from sagemaker_stack import SageMakerStack


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

    members = [
        Member(**row)
        for row in
        csv.DictReader((Path(__file__).parent / 'members.csv').read_text().split('\n'))
    ]

    iam_team = TeamStack(app, 'Team', members, sagemaker.domain.attr_domain_id)

    app.synth()


if __name__ == '__main__':
    main()