from aws_cdk import App
from build_stack import BuildStack
from sagemaker_stack import SageMakerStack

app = App()

build = BuildStack(app, 'Build')

sagemaker = SageMakerStack(app, 'SageMaker')

app.synth()