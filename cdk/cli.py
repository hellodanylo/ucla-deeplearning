import json
import uuid
import clize
import boto3

from cdk.environment import BuildResources, SSMParameter, SageMakerResources


def sagemaker_jupyter_process(*, image_version: str):
    sm = boto3.client('sagemaker', region_name='us-west-2')
    ssm = boto3.client('ssm', region_name='us-west-2')

    environment = json.loads(ssm.get_parameter(Name=SSMParameter.IMAGE_ENVIRONMENT.value)['Parameter']['Value'])

    sagemaker_resources = SageMakerResources.from_json(ssm.get_parameter(Name=SSMParameter.SAGEMAKER_RESOURCES.value)['Parameter']['Value'])
    build_resources = BuildResources.from_json(ssm.get_parameter(Name=SSMParameter.BUILD_RESOURCES.value)['Parameter']['Value'])
    assert isinstance(sagemaker_resources, SageMakerResources)
    assert isinstance(build_resources, BuildResources)

    training_job_name = f'collegium-test-{image_version}-{uuid.uuid4().__str__()[:5]}'

    sm.create_training_job(
        TrainingJobName=training_job_name,
        AlgorithmSpecification={
            'TrainingImage': f'{build_resources.collegium_ecr}:{image_version}',
            'TrainingInputMode': 'File',
            'ContainerArguments': ['python', '-m', 'foundation.cli', 'jupyter-process', '--execute', '01_dnn', '02_cnn', '03_rnn', '04_gan', '05_ensemble'],
            
        },
        Environment=environment,
        RoleArn=sagemaker_resources.sagemaker_role_arn,
        ResourceConfig={
            'InstanceType': 'ml.p3.2xlarge',
            'InstanceCount': 1,
            'VolumeSizeInGB': 100,
        },
        OutputDataConfig={
            'S3OutputPath': f's3://{sagemaker_resources.bucket_public}/app'
        },
        StoppingCondition={
            'MaxRuntimeInSeconds': 60 * 90,
        },
    )
    print("Started", training_job_name)
    sm.get_waiter('training_job_completed_or_stopped').wait(TrainingJobName=training_job_name)
    
    status = sm.describe_training_job(TrainingJobName=training_job_name)['TrainingJobStatus']
    print("Finished", training_job_name, "with status", status)

    if status == "Completed":
        exit(0)
    else:
        exit(1)


if __name__ == '__main__':
    clize.run([sagemaker_jupyter_process])
