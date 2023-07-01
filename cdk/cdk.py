import csv
import os
from pathlib import Path
from aws_cdk import App
from build_stack import BuildStack
from team_stack import TeamStack, Member
from sagemaker_stack import SageMakerStack

app = App()

build = BuildStack(app, 'Build')

sagemaker: SageMakerStack = SageMakerStack(app, 'SageMaker')

members = [
    Member(**row)
    for row in
    csv.DictReader((Path(__file__).parent / 'members.csv').read_text().split('\n'))
]

iam_team = TeamStack(app, 'Team', members, sagemaker.domain.attr_domain_id)

app.synth()