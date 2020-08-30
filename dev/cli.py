#!/usr/bin/env python
import json
import os
import subprocess
from time import sleep
from typing import Optional

import boto3
import clize
import docker
from IPython import embed
from docker.models.containers import Container

project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
container_jupyter = "ucla_jupyter"
notebook_instance_type = "ml.t2.xlarge"
sagemaker_notebook_instance = "danylo-test"
github_repo = "https://github.com/hellodanylo/ucla-deeplearning.git"

aws = boto3.Session(profile_name="ucla")
sagemaker = aws.client("sagemaker")


def find_container_by_name(name) -> Optional[Container]:
    containers = docker.from_env().containers.list()
    for container in containers:
        if container.name == name:
            return container

    return None


def jupyter_start():
    subprocess.run(
        [
            *["docker", "run"],
            *["--name", container_jupyter],
            *["--hostname", container_jupyter],
            *["-v", f"{project_path}:/app/git"],
            *["-v", "ucla_mlflow_backend:/app/mlflow_backend"],
            *["-v", "ucla_jupyter_settings:/root/.local/share/jupyter/runtime"],
            *["-v", "ucla_jupyter_settings:/root/.jupyter"],
            "-d",  # detached mode
            *["--gpus", "all"],  # enable access to CUDA
            "-it",
            container_jupyter,
            "/opt/conda/bin/jupyter",
            "lab",
            "--notebook-dir=/app",
            "--ip=0.0.0.0",
            "--port=80",
            "--no-browser",
            "--allow-root",
        ]
    )


def jupyter_stop():
    container = find_container_by_name(container_jupyter)
    if container is not None:
        container.stop()


def jupyter_down():
    container = find_container_by_name(container_jupyter)
    if container is None:
        return

    if container.status == "running":
        container.stop()

    container.remove()


def jupyter_up():
    jupyter_stop()
    jupyter_start()


def shell():
    embed()


def sagemaker_start():
    if get_notebook_status() == "Stopped":
        sagemaker.start_notebook_instance(
            NotebookInstanceName=sagemaker_notebook_instance
        )

    sagemaker_wait_in_service()


def sagemaker_wait_in_service():
    print("Waiting to be in service...")
    sagemaker.get_waiter("notebook_instance_in_service").wait(
        NotebookInstanceName=sagemaker_notebook_instance
    )
    url = sagemaker.describe_notebook_instance(
        NotebookInstanceName=sagemaker_notebook_instance
    )["Url"]
    print(f"https://{url}/lab")


def sagemaker_stop():
    status = get_notebook_status()

    if status == "InService":
        sagemaker.stop_notebook_instance(
            NotebookInstanceName=sagemaker_notebook_instance
        )
    elif status == "Stopped":
        return
    elif status != "Stopping":
        raise Exception(f"Unexpected notebooks status: {status}")

    print("Waiting to be stopped...")
    sagemaker.get_waiter("notebook_instance_stopped").wait(
        NotebookInstanceName=sagemaker_notebook_instance
    )


def get_notebook_status():
    status = sagemaker.describe_notebook_instance(
        NotebookInstanceName=sagemaker_notebook_instance
    )["NotebookInstanceStatus"]
    return status


def sagemaker_up():
    config = terraform_output()

    params = dict(
        NotebookInstanceName=sagemaker_notebook_instance,
        InstanceType=notebook_instance_type,
        SubnetId=config["subnet_id"],
        SecurityGroupIds=[config["security_group_id"]],
        RoleArn=config["role_arn"],
        LifecycleConfigName=config["sagemaker_lifecycle_name"],
        VolumeSizeInGB=20,
        DefaultCodeRepository=github_repo,
    )

    print(json.dumps(params, indent=True))
    sagemaker.create_notebook_instance(**params)
    sagemaker_wait_in_service()

    sleep(60 * 30)

    sagemaker_stop()
    sagemaker_start()


def sagemaker_down():
    status = get_notebook_status()

    if status == 'InService':
        sagemaker_stop()

    if status == 'Deleted':
        return

    if status != 'Deleting':
        sagemaker.delete_notebook_instance(NotebookInstanceName=sagemaker_notebook_instance)

    print('Waiting to be deleted...')
    sagemaker.get_waiter('notebook_instance_deleted').wait(NotebookInstanceName=sagemaker_notebook_instance)


def terraform_output():
    proc = subprocess.run(
        ["terragrunt", "output", "-json"],
        cwd=os.path.join(project_path, "dev", "aws-sagemaker"),
        capture_output=True,
    )
    text = proc.stdout.decode()
    json_object = json.loads(text)
    output_dict = {k: v['value'] for k, v in json_object.items()}
    return output_dict


clize.run(
    [
        jupyter_start,
        jupyter_stop,
        jupyter_up,
        jupyter_down,
        sagemaker_up,
        sagemaker_start,
        sagemaker_stop,
        sagemaker_down,
        shell,
    ]
)
