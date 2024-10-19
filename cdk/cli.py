#!/usr/bin/env python

import uuid
import clize
import boto3

import collegium.foundation.cli
from collegium.cdk.environment import BuildResources, SSMParameter, SageMakerResources, load_build_resources, load_sagemaker_resources


def sagemaker_jupyter_process(*, image_version: str = 'latest'):
    job_prefix = f'collegium-test-{image_version[:16]}'
    cmd = ['python', '-m', collegium.foundation.cli.__name__, 'jupyter-process', '--execute', 'm01_dnn', 'm02_cnn', 'm03_rnn', 'm04_gan']
    sagemaker_train(*cmd, gpu=True, job_prefix=job_prefix, image_version=image_version)


def sagemaker_train(*cmd, gpu: bool = False, job_prefix: str = 'collegium', image_version: str = 'latest'):
    sm = boto3.client('sagemaker', region_name='us-west-2')
    sagemaker_resources = load_sagemaker_resources()
    build_resources = load_build_resources()

    job_name = f'{job_prefix}-{uuid.uuid4().__str__()[:5]}'

    sm.create_training_job(
        TrainingJobName=job_name,
        AlgorithmSpecification={
            'TrainingImage': f'{build_resources.collegium_ecr}:{image_version}',
            'TrainingInputMode': 'File',
            'ContainerArguments': cmd,
        },
        ResourceConfig={
            'InstanceType': 'ml.g4dn.4xlarge',
            'InstanceCount': 1,
            'VolumeSizeInGB': 100,
        },
        OutputDataConfig={
            'S3OutputPath': f's3://{sagemaker_resources.bucket_public}/app'
        },
        RoleArn=sagemaker_resources.sagemaker_role_arn,
        StoppingCondition={
             'MaxRuntimeInSeconds': 60 * 90,
        },
    )
    print("Started", job_name)
    sm.get_waiter('training_job_completed_or_stopped').wait(TrainingJobName=job_name)
    
    status = sm.describe_training_job(TrainingJobName=job_name)['TrainingJobStatus']
    print("Finished", job_name, "with status", status)

    if status == "Completed":
        exit(0)
    else:
        exit(1)


def sagemaker_process(*cmd, gpu: bool = False, job_prefix: str = 'collegium', image_version: str = 'latest'):
    sm = boto3.client('sagemaker', region_name='us-west-2')
    ssm = boto3.client('ssm', region_name='us-west-2')

    sagemaker_resources = SageMakerResources.from_json(ssm.get_parameter(Name=SSMParameter.SAGEMAKER_RESOURCES.value)['Parameter']['Value'])
    build_resources = BuildResources.from_json(ssm.get_parameter(Name=SSMParameter.BUILD_RESOURCES.value)['Parameter']['Value'])
    assert isinstance(sagemaker_resources, SageMakerResources)
    assert isinstance(build_resources, BuildResources)

    job_name = f'{job_prefix}-{uuid.uuid4().__str__()[:5]}'

    sm.create_processing_job(
        ProcessingJobName=job_name,
        AppSpecification={
            'ImageUri': f'{build_resources.collegium_ecr}:{image_version}',
            'ContainerArguments': cmd,
        },
        RoleArn=sagemaker_resources.sagemaker_role_arn,
        ProcessingResources={
            'ClusterConfig': {
                'InstanceType': 'ml.c4.2xlarge' if not gpu else 'ml.p3.2xlarge',
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
    clize.run([sagemaker_process, sagemaker_jupyter_process])
