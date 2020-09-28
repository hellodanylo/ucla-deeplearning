#!/usr/bin/env python
import docker
import json
import os
import subprocess
from functools import lru_cache
from time import sleep
from typing import Optional

import boto3
import clize
import dotenv
from IPython import embed
from docker.models.containers import Container

project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
container_jupyter = "ucla-jupyter"
image_jupyter = "ucla_jupyter"
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


def find_container_by_name(name, remote: bool = False) -> Optional[Container]:
    docker_host = (
        "unix:///var/run/docker.sock"
        if not remote
        else f"unix://{project_path}/dev/aws-ec2/docker.sock"
    )
    containers = docker.DockerClient(base_url=docker_host).containers.list(all=True)
    for container in containers:
        if container.name == name:
            return container

    return None


def jupyter_start(gpu: bool = False, instructor: bool = False, remote: bool = False):
    """
    Starts the Jupyter container

    :param gpu:
    :param instructor:
    :param remote:
    :return:
    """
    docker_cli(
        "run",
        *["--name", container_jupyter],
        *["--hostname", container_jupyter],
        *(
            [
                "-v",
                f"{project_path}:/app/ucla_deeplearning"
                if not remote
                else "ucla_jupyter_git:/app/ucla_deeplearning",
            ]
        ),
        *["-v", "ucla_jupyter_settings:/root/.local/share/jupyter/runtime"],
        *["-v", "ucla_jupyter_ssh:/root/.ssh"],
        *["-v", "ucla_jupyter_keras:/root/.keras"],
        *["-v", f"{os.environ['HOME']}/.aws:/root/.aws"],
        *(
            [
                "-v",
                f"{os.environ['HOME']}/git/lab/ucla-deeplearning-instructor:/app/ucla_deeplearning/instructor",
            ]
            if instructor
            else []
        ),
        "-p",
        "3000:80",
        "-d",  # detached mode
        *(["--gpus", "all"] if gpu else []),
        "-it",
        image_jupyter,
        "/opt/conda/bin/jupyter",
        "lab",
        "--notebook-dir=/app",
        "--ip=0.0.0.0",
        "--port=80",
        "--no-browser",
        "--allow-root",
        remote=remote,
    )
    sleep(5)

    docker_cli("exec", container_jupyter, "jupyter", "notebook", "list", remote=remote)
    print("Jupyter available at http://localhost:3000 - token can be found above.")


def jupyter_stop(remote: bool = False):
    """
    Stops the Jupyter container

    :param remote:
    :return:
    """
    container = find_container_by_name(container_jupyter, remote=remote)
    if container is not None:
        container.stop()


def jupyter_down(*, remote: bool = False, quiet: bool = False):
    """
    Stops and removes the Jupyter container

    :param quiet:
    :param remote:
    :return:
    """
    container = find_container_by_name(container_jupyter, remote=remote)
    if container is None:
        if not quiet:
            print("No container found")
        return

    if container.status == "running":
        container.stop()

    container.remove()

    if not quiet:
        print(f"Removed {container.name}")


def docker_cli(*cmd, remote: bool = False):
    run(
        [
            "docker",
            *(
                ["-H", f"unix://{project_path}/dev/aws-ec2/docker.sock"]
                if remote
                else []
            ),
            *cmd,
        ]
    )


def jupyter_up(*, gpu: bool = False, instructor: bool = False, remote: bool = False, init: bool = False):
    """
    Builds and starts the Jupyter container
    """
    jupyter_build(instructor=instructor, remote=remote, init=init)
    jupyter_down(remote=remote, quiet=True)
    jupyter_start(gpu=gpu, instructor=instructor, remote=remote)


def jupyter_build(
    *, instructor: bool = False, remote: bool = False, init: bool = False
):
    docker_cli(
        "build",
        "-t",
        image_jupyter,
        "--build-arg",
        f"CONDA_RC={'condarc_instructor.yml' if instructor else 'condarc_student.yml'}",
        "--build-arg",
        f"CONDA_ENV={'conda_init.yml' if init else 'conda_lock.yml'}",
        *(["--network", "shell_docker_primary"] if instructor else []),
        os.path.join(project_path, "dev", "docker-jupyter"),
        remote=remote,
    )


def shell():
    embed(colors="neutral")


def sagemaker_resize(instance_type):
    """
    Resizes the SageMaker notebook (will restart notebook if already started)

    :param instance_type:
    :return:
    """
    old_instance_type = get_notebook_instance_type()
    if old_instance_type == instance_type:
        print(f"The instance type is already {instance_type}")
        return

    if get_notebook_status() != "stopped":
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
    """
    Start the SageMaker notebook

    :return:
    """
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
    """
    Stops the SageMaker notebook

    :param force:
    :return:
    """
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
    """
    Creates and starts the SageMaker notebook

    :param instance_type:
    :param storage_gb:
    :return:
    """
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
    """
    Stops and removes the SageMaker notebook

    :return:
    """
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
    """
    Configures the AWS account access

    :return:
    """
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
    """
    Creates an S3 bucket needed to run SageMaker notebook

    :return:
    """
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
    """
    Removes the S3 bucket needed to run SageMaker notebook

    :return:
    """
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


def terraform_output_ec2():
    return terraform_output("aws-ec2", env={"s3_bucket_name": s3_bucket_name()})


def dynamodb_set_notebook_state(name: str, state: str):
    db = boto_session().client("dynamodb")
    db.put_item(
        TableName=terraform_output_sagemaker()["dynamodb_table_name"],
        Item={"name": {"S": name}, "state": {"S": state}},
    )


def ec2_up():
    bucket_name = s3_bucket_name()

    run(
        ["terragrunt", "apply", "-auto-approve",],
        cwd=os.path.join(project_path, "dev", "aws-ec2"),
        env={"s3_bucket_name": bucket_name},
    )


def ec2_ssh(*cmd):
    connection = terraform_output("aws-ec2", env={"s3_bucket_name": s3_bucket_name()})[
        "ec2"
    ]
    instances = (
        boto_session()
        .client("ec2")
        .describe_instances(InstanceIds=[connection["instance_id"]])
    )
    ip = instances["Reservations"][0]["Instances"][0]["NetworkInterfaces"][0][
        "Association"
    ]["PublicIp"]
    key_path = f"{project_path}/dev/aws-ec2/key.private"
    username = connection["username"]

    args = [
        "ssh",
        "-i",
        key_path,
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        *cmd,
        f"{username}@{ip}",
    ]

    print(f"Running {args}")
    subprocess.run(args)


def ec2_tunnel():
    local_docker_path = f"{project_path}/dev/aws-ec2/docker.sock"

    cmd = [
        "-L",
        f"{local_docker_path}:/var/run/docker.sock",
        "-L",
        "5000:localhost:3000",
    ]

    subprocess.run(["rm", "-f", local_docker_path])
    ec2_ssh(*cmd)
    subprocess.run(["rm", "-f", local_docker_path])


def ec2_start():
    instance_id = terraform_output_ec2()["ec2"]["instance_id"]

    boto_session().client("ec2").start_instances(InstanceIds=[instance_id])
    ec2_wait_started(instance_id)


def ec2_wait_started(instance_id: str):
    print("Waiting to be running...")
    waiter = boto_session().client("ec2").get_waiter("instance_running")
    waiter.wait(InstanceIds=[instance_id])
    print("Running")


def ec2_stop():
    instance_id = terraform_output_ec2()["ec2"]["instance_id"]

    ec2 = boto_session().client("ec2")
    ec2.stop_instances(InstanceIds=[instance_id])

    print("Waiting to stop...")
    waiter = ec2.get_waiter("instance_stopped")
    waiter.wait(InstanceIds=[instance_id])
    print("Stopped")


def dynamodb_get_notebook_state(name: str):
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
            jupyter_up,
            jupyter_start,
            jupyter_stop,
            jupyter_down,
            aws_init,
            s3_up,
            s3_down,
            sagemaker_up,
            sagemaker_start,
            sagemaker_stop,
            sagemaker_resize,
            sagemaker_down,
            jupyter_build,
            docker_cli,
            terraform_output_sagemaker,
            terraform_output_ec2,
            ec2_up,
            ec2_ssh,
            ec2_tunnel,
            ec2_start,
            shell,
        ]
    )
