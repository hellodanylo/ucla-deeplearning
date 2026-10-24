#!/usr/bin/env python

import uuid
from typing import Dict, Optional, Sequence

import clize
import boto3

from collegium.cdk.environment import BuildResources, SSMParameter, SageMakerResources, load_build_resources, load_sagemaker_resources


GITHUB_REPO = 'https://github.com/hellodanylo/ucla-deeplearning'
# Must match COLLEGIUM_ROOT in foundation/jupyter_render.py and the import symlink in the Studio image
CHECKOUT = '/home/sagemaker-user/collegium'


def sagemaker_jupyter_process(*, image_version: str, git_commit: str, backends: str = 'tensorflow,torch'):
    """Executes all module notebooks of `git_commit` (fetched from GitHub) in the Studio image `image_version`,
    as one training job per Keras backend (comma-separated `backends`), run in parallel."""
    script = ' && '.join([
        f'git init -q {CHECKOUT}',
        f'cd {CHECKOUT}',
        f'git fetch -q --depth 1 {GITHUB_REPO} {git_commit}',
        'git checkout -q FETCH_HEAD',
        'python -m collegium.foundation.cli jupyter-process --execute m01_dnn m02_cnn m03_rnn m04_gan m05_ensemble',
    ])
    # Container arguments are limited to 256 characters each, environment values to 512
    jobs = [
        start_training_job(
            'bash', '-c', 'eval "$COLLEGIUM_TEST_SCRIPT"',
            # Notebooks select the backend with os.environ.setdefault("KERAS_BACKEND", ...)
            environment={'COLLEGIUM_TEST_SCRIPT': script, 'KERAS_BACKEND': backend},
            job_prefix=f'collegium-test-{git_commit[:16]}-{backend[:5]}', image_version=image_version,
        )
        for backend in backends.split(',')
    ]
    exit(0 if wait_training_jobs(jobs) else 1)


def start_training_job(*cmd, environment: Optional[Dict[str, str]] = None,
                       job_prefix: str = 'collegium', image_version: str = 'latest') -> str:
    environment = environment or {}
    assert all(len(a) <= 256 for a in cmd), 'SageMaker limits each container argument to 256 characters'
    assert all(len(v) <= 512 for v in environment.values()), 'SageMaker limits environment values to 512 characters'
    sm = boto3.client('sagemaker', region_name='us-west-2')
    sagemaker_resources = load_sagemaker_resources()
    build_resources = load_build_resources()

    job_name = f'{job_prefix}-{uuid.uuid4().__str__()[:5]}'

    sm.create_training_job(
        TrainingJobName=job_name,
        AlgorithmSpecification={
            'TrainingImage': f'{build_resources.collegium_ecr}:{image_version}',
            'TrainingInputMode': 'File',
            'ContainerArguments': list(cmd),
        },
        Environment=environment,
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
    return job_name


def wait_training_jobs(job_names: Sequence[str]) -> bool:
    """Waits for all jobs to finish; True if all completed successfully."""
    sm = boto3.client('sagemaker', region_name='us-west-2')
    ok = True
    for job_name in job_names:
        sm.get_waiter('training_job_completed_or_stopped').wait(
            TrainingJobName=job_name, WaiterConfig={'Delay': 60, 'MaxAttempts': 240})
        job = sm.describe_training_job(TrainingJobName=job_name)
        print("Finished", job_name, "with status", job['TrainingJobStatus'], job.get('FailureReason', ''))
        ok = ok and job['TrainingJobStatus'] == 'Completed'
    return ok


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
            'ContainerArguments': list(cmd),
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
