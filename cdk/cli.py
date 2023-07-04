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

    job_name = f'collegium-test-{image_version}-{uuid.uuid4().__str__()[:5]}'

    sm.create_processing_job(
        ProcessingJobName=job_name,
        AppSpecification={
            'ImageUri': f'{build_resources.collegium_ecr}:{image_version}',
            'ContainerArguments': ['python', '-m', 'collegium.foundation.cli', 'jupyter-process', '--execute', 'm01_dnn', 'm02_cnn', 'm03_rnn', 'm04_gan', 'm05_ensemble'],
        },
        Environment=environment,
        RoleArn=sagemaker_resources.sagemaker_role_arn,
        ProcessingResources={
            'ClusterConfig': {
                'InstanceType': 'ml.p3.2xlarge',
                'InstanceCount': 1,
                'VolumeSizeInGB': 100,
            },
        },
        StoppingCondition={
            'MaxRuntimeInSeconds': 60 * 90,
        },
    )
    print("Started", job_name)
    sm.get_waiter('processing_job_completed_or_stopped').wait(ProcessingJobName=job_name)
    
    status = sm.describe_processing_job(ProcessingJobName=job_name)['ProcessingJobStatus']
    print("Finished", job_name, "with status", status)

    if status == "Completed":
        exit(0)
    else:
        exit(1)


if __name__ == '__main__':
    clize.run([sagemaker_jupyter_process])
