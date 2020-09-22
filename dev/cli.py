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
            "--rm",  # remove after stopping
            *["-v", f"{project_path}:/app/ucla_deeplearning"],
            *["-v", "ucla_mlflow_backend:/app/mlflow_backend"],
            *["-v", "ucla_jupyter_settings:/root/.local/share/jupyter/runtime"],
            *["-v", "ucla_jupyter_settings:/root/.jupyter"],
            *["-v", "ucla_jupyter_keras:/root/.keras"],
            *["-v", f"{os.environ['HOME']}/.aws:/root/.aws"],
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

    sleep(5)

    subprocess.run(["docker", "exec", container_jupyter, "jupyter", "notebook", "list"])
    print("Jupyter available at http://localhost:3000 - token can be found above.")


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


def jupyter_build():
    run(
        [
            "docker",
            "build",
            "-t",
            container_jupyter,
            os.path.join(project_path, "dev", "docker-jupyter"),
        ]
    )


def jupyter_up(*, gpu=False):
    jupyter_build()
    jupyter_stop()
    jupyter_start(gpu=gpu)


def shell():
    embed()


def sagemaker_resize(instance_type):
    old_instance_type = get_notebook_instance_type()
    if old_instance_type == instance_type:
        print(f"The instance type is already {instance_type}")
        return

    if get_notebook_status() != 'stopped':
        should_start = True
        sagemaker_stop()
    else:
        should_start = False

    boto_sagemaker().update_notebook_instance(
        NotebookInstanceName=sagemaker_notebook_name(), InstanceType=instance_type
    )
    print("Waiting for the notebook to finish resizing...")
    sagemaker_wait_stopped(quiet=True)
    print(f"Changed instance type from {old_instance_type} to {instance_type}")

    if should_start:
        sagemaker_start()


def sagemaker_start():
    instance_name = sagemaker_notebook_name()

    if get_notebook_status() == "Stopped":
        boto_sagemaker().start_notebook_instance(NotebookInstanceName=instance_name)

    sagemaker_wait_in_service()
    sagemaker_print_url()


def sagemaker_print_url():
    url = f"https://us-west-2.console.aws.amazon.com/sagemaker/home?region=us-west-2#/notebook-instances/openNotebook/{sagemaker_notebook_name()}?view=lab"
    print(url)


def sagemaker_wait_in_service():
    name = sagemaker_notebook_name()
    print(f"Waiting for notebook {name} to be in service...")
    boto_sagemaker().get_waiter("notebook_instance_in_service").wait(
        NotebookInstanceName=name
    )


def sagemaker_wait_stopped(quiet=False):
    name = sagemaker_notebook_name()

    if not quiet:
        print(f"Waiting for notebook {name} to be stopped (about 1 minute)...")

    boto_sagemaker().get_waiter("notebook_instance_stopped").wait(
        NotebookInstanceName=name
    )


def sagemaker_stop(force=False):
    status = get_notebook_status()

    name = sagemaker_notebook_name()
    if status == "InService":
        if not force:
            confirm = input(
                "All unsaved changes are lost when the notebook is stopped. Confirm? [y/n]: "
            )
            if confirm != "y":
                return
        boto_sagemaker().stop_notebook_instance(NotebookInstanceName=name)
    elif status == "Stopped":
        return
    elif status != "Stopping":
        raise Exception(f"Unexpected {name} notebook status: {status}")

    sagemaker_wait_stopped()


def get_notebook_instance_type():
    instance_type = boto_sagemaker().describe_notebook_instance(
        NotebookInstanceName=sagemaker_notebook_name()
    )["InstanceType"]
    return instance_type


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


def sagemaker_up(instance_type="ml.t2.xlarge", storage_gb=20):
    notebook_name = sagemaker_notebook_name()
    bucket_name = s3_bucket_name()

    run(
        [
            "terragrunt",
            "apply",
            "-auto-approve",
            "-var",
            f"sagemaker_notebook_name={notebook_name}",
        ],
        cwd=os.path.join(project_path, "dev", "aws-sagemaker"),
        env={"s3_bucket_name": bucket_name},
    )

    sagemaker_output = terraform_output(
        "aws-sagemaker", env={"s3_bucket_name": bucket_name}
    )

    params = dict(
        NotebookInstanceName=notebook_name,
        InstanceType=instance_type,
        SubnetId=sagemaker_output["subnet_id"],
        SecurityGroupIds=[sagemaker_output["security_group_id"]],
        RoleArn=sagemaker_output["role_arn"],
        LifecycleConfigName=sagemaker_output["sagemaker_lifecycle_name"],
        VolumeSizeInGB=storage_gb,
        DefaultCodeRepository=github_repo,
    )

    dynamodb_set_notebook_state(notebook_name, "created")

    print(json.dumps(params, indent=True))
    boto_sagemaker().create_notebook_instance(**params)
    sagemaker_wait_in_service()

    while dynamodb_get_notebook_state(notebook_name) == "created":
        print(
            "Waiting for notebook environment to finish installation (about 20 minutes)..."
        )
        sleep(60)

    sagemaker_stop(force=True)
    sagemaker_start()


def sagemaker_down():
    status = get_notebook_status()

    if status != "Deleted":
        confirm = input(
            "Are files saved in the notebook will be lost when the notebook is deleted. Confirm [y/n]: "
        )
        if confirm != "y":
            return

        if status == "InService":
            sagemaker_stop(force=True)

        if status != "Deleting":
            boto_sagemaker().delete_notebook_instance(
                NotebookInstanceName=sagemaker_notebook_name()
            )

        sagemaker_wait_deleted()

    name = sagemaker_notebook_name()

    run(
        [
            "terragrunt",
            "destroy",
            "-auto-approve",
            "-var",
            f"sagemaker_notebook_name={name}",
        ],
        cwd=os.path.join(project_path, "dev", "aws-sagemaker"),
        env={"s3_bucket_name": s3_bucket_name()},
    )


def sagemaker_wait_deleted():
    name = sagemaker_notebook_name()
    print(f"Waiting {name} for to be deleted (about 2 minutes)...")
    boto_sagemaker().get_waiter("notebook_instance_deleted").wait(
        NotebookInstanceName=name
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

    subprocess.run(["aws", "--profile", "ucla", "configure"])

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
            f"s3_bucket_name={s3_bucket_name()}",
        ],
        cwd=os.path.join(project_path, "dev", "aws-s3"),
    )


def terraform_output_sagemaker():
    return terraform_output("aws-sagemaker", env={"s3_bucket_name": s3_bucket_name()})


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


if __name__ == "__main__":
    clize.run(
        [
            jupyter_build,
            jupyter_start,
            jupyter_stop,
            jupyter_up,
            jupyter_down,
            aws_init,
            sagemaker_up,
            sagemaker_start,
            sagemaker_stop,
            sagemaker_down,
            sagemaker_resize,
            s3_up,
            s3_down,
            shell,
        ]
    )
