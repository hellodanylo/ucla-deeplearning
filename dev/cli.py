#!/usr/bin/env python

import json
import os
import subprocess
from functools import lru_cache
from time import sleep
from typing import Optional

import boto3
import clize
import docker
import dotenv
from IPython import embed
from docker.models.containers import Container

project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
container_jupyter = "ucla_jupyter"
github_repo = "https://github.com/hellodanylo/ucla-deeplearning.git"
project_env_path = os.path.join(project_path, "dev", "cli.env")


@lru_cache()
def boto_session():
    return boto3.Session(profile_name="ucla")


@lru_cache()
def boto_sagemaker():
    return boto_session().client("sagemaker")


@lru_cache()
def sagemaker_notebook_name():
    project_user = dotenv.dotenv_values(dotenv_path=project_env_path).get(
        "PROJECT_USER"
    )
    return f"ucla-deep-learning-{project_user}"


@lru_cache()
def s3_bucket_name():
    project_user = dotenv.dotenv_values(dotenv_path=project_env_path).get(
        "PROJECT_USER"
    )
    return f"ucla-deep-learning-{project_user}-private"


def find_container_by_name(name) -> Optional[Container]:
    containers = docker.from_env().containers.list(all=True)
    for container in containers:
        if container.name == name:
            return container

    return None


def jupyter_start(gpu: bool = False):
    subprocess.run(
        [
            *["docker", "run"],
            *["--name", container_jupyter],
            *["--hostname", container_jupyter],
            *["-v", f"{project_path}:/app/ucla_deeplearning"],
            *["-v", "ucla_mlflow_backend:/app/mlflow_backend"],
            *["-v", "ucla_jupyter_settings:/root/.local/share/jupyter/runtime"],
            *["-v", "ucla_jupyter_settings:/root/.jupyter"],
            "-p",
            "3000:80",
            "-d",  # detached mode
            *(["--gpus", "all"] if gpu else []),
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

    print("Jupyter available")


def jupyter_stop():
    container = find_container_by_name(container_jupyter)
    if container is not None:
        container.stop()


def jupyter_down():
    container = find_container_by_name(container_jupyter)
    if container is None:
        print("No container found")
        return

    if container.status == "running":
        container.stop()

    container.remove()
    print(f"Removed {container.name}")


def jupyter_up():
    run(
        [
            "docker",
            "build",
            "-t",
            "ucla_jupyter",
            os.path.join(project_path, "dev", "docker-jupyter"),
        ]
    )

    jupyter_stop()
    jupyter_start()


def shell():
    embed()


def sagemaker_start():
    if get_notebook_status() == "Stopped":
        boto_sagemaker().start_notebook_instance(
            NotebookInstanceName=sagemaker_notebook_name()
        )

    sagemaker_wait_in_service()
    sagemaker_print_url()


def sagemaker_print_url():
    url = boto_sagemaker().describe_notebook_instance(
        NotebookInstanceName=sagemaker_notebook_name()
    )["Url"]
    print(f"https://{url}/lab")


def sagemaker_wait_in_service():
    name = sagemaker_notebook_name()
    print(f"Waiting for notebook {name} to be in service...")
    boto_sagemaker().get_waiter("notebook_instance_in_service").wait(
        NotebookInstanceName=name
    )


def sagemaker_stop():
    status = get_notebook_status()

    name = sagemaker_notebook_name()
    if status == "InService":
        boto_sagemaker().stop_notebook_instance(
            NotebookInstanceName=name
        )
    elif status == "Stopped":
        return
    elif status != "Stopping":
        raise Exception(f"Unexpected {name} notebook status: {status}")

    print(f"Waiting for notebook {name} to be stopped (about 1 minute)...")
    boto_sagemaker().get_waiter("notebook_instance_stopped").wait(
        NotebookInstanceName=name
    )


def get_notebook_status():
    status = boto_sagemaker().describe_notebook_instance(
        NotebookInstanceName=sagemaker_notebook_name()
    )["NotebookInstanceStatus"]
    return status


def run(args, cwd=None, capture_output=False, env=None):
    if cwd is None:
        cwd = os.getcwd()

    print(f"Running in {cwd}: {args}")

    if env is None:
        sub_env = None
    else:
        sub_env = os.environ.copy()
        sub_env.update(env)

    return subprocess.run(
        args, cwd=cwd, capture_output=capture_output, env=sub_env, check=True
    )


def sagemaker_up(instance_type="ml.t2.xlarge"):
    s3_output = terraform_output("aws-s3")
    name = sagemaker_notebook_name()

    run(
        ["terragrunt", "apply", "-auto-approve", "-var", f"sagemaker_notebook_name={name}"],
        cwd=os.path.join(project_path, "dev", "aws-sagemaker"),
        env=s3_output,
    )

    sagemaker_output = terraform_output("aws-sagemaker", env=s3_output)

    params = dict(
        NotebookInstanceName=name,
        InstanceType=instance_type,
        SubnetId=sagemaker_output["subnet_id"],
        SecurityGroupIds=[sagemaker_output["security_group_id"]],
        RoleArn=sagemaker_output["role_arn"],
        LifecycleConfigName=sagemaker_output["sagemaker_lifecycle_name"],
        VolumeSizeInGB=20,
        DefaultCodeRepository=github_repo,
    )

    dynamodb_set_notebook_state(name, 'created')

    print(json.dumps(params, indent=True))
    boto_sagemaker().create_notebook_instance(**params)
    sagemaker_wait_in_service()

    while dynamodb_get_notebook_state(name) == 'created':
        print('Waiting for notebook environment to finish installation (about 20 minutes)...')
        sleep(60)

    sagemaker_stop()
    sagemaker_start()
    sagemaker_print_url()


def sagemaker_down():
    status = get_notebook_status()

    if status != "Deleted":
        if status == "InService":
            sagemaker_stop()

        if status != "Deleting":
            boto_sagemaker().delete_notebook_instance(
                NotebookInstanceName=sagemaker_notebook_name()
            )

        sagemaker_wait_deleted()

    s3_output = terraform_output("aws-s3")
    name = sagemaker_notebook_name()

    run(
        ["terragrunt", "destroy", "-auto-approve", "-var", f"sagemaker_notebook_name={name}"],
        cwd=os.path.join(project_path, "dev", "aws-sagemaker"),
        env=s3_output,
    )


def sagemaker_wait_deleted():
    print("Waiting for to be deleted...")
    boto_sagemaker().get_waiter("notebook_instance_deleted").wait(
        NotebookInstanceName=sagemaker_notebook_name()
    )


def terraform_output(module, env=None):
    proc = run(
        ["terragrunt", "output", "-json"],
        cwd=os.path.join(project_path, "dev", module),
        capture_output=True,
        env=env,
    )
    text = proc.stdout.decode()
    json_object = json.loads(text)
    output_dict = {k: v["value"] for k, v in json_object.items()}
    return output_dict


def aws_init():
    new_project_user = input("Enter project user name: ")
    with open(os.path.join(project_path, "dev", "cli.env"), "w") as f:
        f.write(f"PROJECT_USER={new_project_user}")

    try:
        user = boto_session().client("iam").list_account_aliases()["AccountAliases"][0]
    except Exception as e:
        raise Exception("Unable to find `ucla` profile in AWS config") from e

    print(f"Found account in AWS config: {user}")
    print(f"S3 Bucket Name = {s3_bucket_name()}")
    print(f"SageMaker Notebook Name = {sagemaker_notebook_name()}")


def s3_up():
    run(
        [
            "terragrunt",
            "apply",
            "-auto-approve",
            "-var",
            f"s3_bucket_name={s3_bucket_name()}",
        ],
        cwd=os.path.join(project_path, "dev", "aws-s3"),
    )


def s3_down():
    run(
        [
            "terragrunt",
            "destroy",
            "-auto-approve",
            "-var",
            f"project_user={s3_bucket_name()}",
        ],
        cwd=os.path.join(project_path, "dev", "aws-s3"),
    )


def terraform_output_sagemaker():
    s3_output = terraform_output("aws-s3")
    return terraform_output("aws-sagemaker", env=s3_output)


def dynamodb_set_notebook_state(name: str, state: str):
    db = boto_session().client("dynamodb")
    db.put_item(
        TableName=terraform_output_sagemaker()["dynamodb_table_name"],
        Item={"name": {"S": name}, "state": {"S": state}},
    )


def dynamodb_get_notebook_state(name):
    db = boto_session().client("dynamodb")
    response = db.get_item(
        TableName=terraform_output_sagemaker()["dynamodb_table_name"],
        Key={"name": {"S": name}},
        ConsistentRead=True,
    )

    return response["Item"]["state"]["S"]


if __name__ == '__main__':
    clize.run(
        [
            jupyter_start,
            jupyter_stop,
            jupyter_up,
            jupyter_down,
            aws_init,
            sagemaker_up,
            sagemaker_start,
            sagemaker_stop,
            sagemaker_down,
            s3_up,
            s3_down,
            shell,
        ]
    )
