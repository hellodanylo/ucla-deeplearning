#!/usr/bin/env python
import re
import tempfile
from base64 import b64decode
from enum import Enum

import docker
import json
import os
import subprocess
from functools import lru_cache
from time import sleep
from typing import Optional, Sequence, Mapping

import boto3
import clize
import dotenv
from IPython import embed
from docker.models.containers import Container

project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
container_jupyter = "ucla-jupyter"
image_jupyter = "ghcr.io/hellodanylo/ucla-deeplearning:master"
github_repo = "https://github.com/hellodanylo/ucla-deeplearning.git"


class NotebookStatus(Enum):
    Pending = 'Pending'
    InService = 'InService'
    Stopping = 'Stopping'
    Stopped = 'Stopped'
    Failed = 'Failed'
    Deleting = 'Deleting'
    Updating = 'Updating'


def load_env():
    project_env_path = os.path.join(project_path, "dev", "cli.env")
    if os.path.exists(project_env_path):
        dotenv.load_dotenv(project_env_path, override=True)


@lru_cache()
def boto_session():
    # us-east-1 is the default for compatibility with the existing AWS Educate installations
    return boto3.Session(region_name=os.environ.get('AWS_REGION', 'us-east-1'))


@lru_cache()
def boto_sagemaker():
    return boto_session().client("sagemaker")


def sagemaker_notebook_name(project_user: Optional[str] = None):
    if project_user is None:
        project_user = os.environ["PROJECT_USER"]
    return f"ucla-deeplearning-{project_user}"


@lru_cache()
def s3_bucket_name():
    project_user = os.environ["PROJECT_USER"]
    return f"ucla-deep-learning-{project_user}-private"


def s3_bucket_region():
    return "us-west-2"


def find_container_by_name(name, remote: bool = False) -> Optional[Container]:
    containers = docker.DockerClient().containers.list(all=True)
    for container in containers:
        if container.name == name:
            return container

    return None


def jupyter_create(
        gpu: bool = False, 
        instructor: bool = False, 
        remote: bool = False, 
        ip: Optional[str] = None, 
        network: Optional[str] = None
    ):
    """
    Starts the Jupyter container

    :param gpu:
    :param instructor:
    :param remote:
    :return:
    """
    docker_cli(
        "create",
        *["--name", container_jupyter],
        *["--hostname", container_jupyter],
        *(
            [
                "-v",
                f"{project_path}:/app/ucla-deeplearning"
                if not remote
                else "/home/ubuntu/ucla-deeplearning:/app/ucla-deeplearning",
            ]
        ),
        *["-v", "ucla_jupyter_settings:/root/.local/share/jupyter/runtime"],
        *["-v", "ucla_jupyter_ssh:/root/.ssh"],
        *["-v", "ucla_jupyter_keras:/root/.keras"],
        *["-v", f"{os.environ['HOME']}/.aws:/root/.aws"],
        *(
            [
                "-v",
                f"{os.environ['HOME']}/git/lab/ucla-deeplearning-instructor:/app/ucla-deeplearning/instructor",
            ]
            if instructor
            else []
        ),
        *(("--ip", ip) if ip is not None else []),
        *(("--network", network) if network is not None else []),
        "-p",
        "3000:80",
        *(["--gpus", "all"] if gpu else []),
        "-it",
        image_jupyter,
        remote=remote,
    )


def jupyter_up(
    *,
    gpu: bool = False,
    instructor: bool = False,
    ip: str = None,
    network: str = None,
    no_pull: bool = False
):
    """
    Creates and starts the Jupyter container
    """
    if not no_pull:
        jupyter_pull()
    jupyter_down(quiet=True)
    jupyter_create(gpu=gpu, instructor=instructor, ip=ip, network=network)
    jupyter_start()


def jupyter_start(*, remote: bool = False):
    """
    Starts the Jupyter container

    :param remote:
    :return:
    """
    docker_cli("start", container_jupyter, remote=remote)
    sleep(10)
    proc = docker_cli("exec", container_jupyter, "jupyter", "lab", "list", remote=remote, capture_output=True)
    token = re.findall('token=([a-zA-Z0-9]+)', proc.stdout.decode())[0]

    print(
        f"Jupyter available at http://localhost:{'5000' if remote else '3000'}/?token={token}"
    )


def jupyter_stop(remote: bool = False):
    """
    Stops the Jupyter container

    :param remote:
    :return:
    """
    container = find_container_by_name(container_jupyter, remote=remote)
    if container is not None:
        container.stop()
        print("Stopped the Jupyter container")


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


def docker_cli(
    *cmd, remote: bool = False, capture_output: bool = False,
) -> subprocess.CompletedProcess:

    return run(
        [
            "docker",
            *(
                ["-H", f"unix://{project_path}/dev/aws-ec2/docker.sock"]
                if remote
                else []
            ),
            *cmd,
        ],
        capture_output=capture_output
    )


def jupyter_pull():
    docker_cli(
        "pull",
        image_jupyter
    )


def jupyter_build(
    *,
    remote: bool = False,
    conda_init: bool = False,
    conda_cache: bool = False,
    vim: bool = False,
    docker_cache_off: bool = False,
):
    docker_cli(
        "build",
        "--pull",
        "--platform", "linux/amd64",
        *(['--no-cache'] if docker_cache_off else []),
        "-t",
        image_jupyter,
        "--build-arg",
        f"CONDA_JUPYTER_ENV={'conda_jupyter_init.yml' if conda_init else 'conda_jupyter_lock.yml'}",
        "--build-arg",
        f"CONDA_DEEPLEARNING_ENV={'conda_deeplearning_init.yml' if conda_init else 'conda_deeplearning_lock.yml'}",
        "--build-arg",
        f"VIM={'true' if vim else 'false'}",
        *(["--network", "inception"] if conda_cache else []),
        os.path.join(project_path, "dev", "docker-jupyter"),
        remote=remote,
    )


def shell():
    """
    Starts an IPython shell in the ucla-dev environment.

    :return:
    """
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

    if sagemaker_notebook_status() != NotebookStatus.Stopped:
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

    if sagemaker_notebook_status(instance_name) == NotebookStatus.Stopped:
        boto_sagemaker().start_notebook_instance(NotebookInstanceName=instance_name)

    sagemaker_wait_in_service()
    sagemaker_print_url()


def read_members():
    from csv import DictReader
    with open(f'{project_path}/dev/members.csv', 'r') as f:
        return list(DictReader(f))


def sagemaker_team_start():
    for member in read_members():
        instance_name = sagemaker_notebook_name(member['name'])
        status = sagemaker_notebook_status(instance_name)
        if status == NotebookStatus.Stopped:
            print(f"Will start {instance_name}")
            boto_sagemaker().start_notebook_instance(NotebookInstanceName=instance_name)
        elif status != NotebookStatus.InService:
            print(f"Skipped {instance_name} in {status}")


def sagemaker_team_stop():
    for member in read_members():
        instance_name = sagemaker_notebook_name(member['name'])
        status = sagemaker_notebook_status(instance_name)
        if status == NotebookStatus.InService:
            print(f"Will stop {instance_name}")
            boto_sagemaker().stop_notebook_instance(NotebookInstanceName=instance_name)
        elif status != NotebookStatus.Stopped:
            print(f"Skipping {instance_name} in {status}")


def sagemaker_print_url():
    url = f"https://{os.environ['AWS_REGION']}.console.aws.amazon.com/sagemaker/home?region={os.environ['AWS_REGION']}#/notebook-instances/openNotebook/{sagemaker_notebook_name()}?view=lab"
    print(url)


def sagemaker_wait_in_service():
    name = sagemaker_notebook_name()
    print(f"Waiting for notebook {name} to be running...")
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
    status = sagemaker_notebook_status()

    name = sagemaker_notebook_name()
    if status == NotebookStatus.InService:
        if not force:
            confirm = input(
                "All unsaved changes are lost when the notebook is stopped. Confirm? [y/n]: "
            )
            if confirm != "y":
                return
        boto_sagemaker().stop_notebook_instance(NotebookInstanceName=name)
    elif status == NotebookStatus.Stopped:
        return
    elif status != NotebookStatus.Stopping:
        raise Exception(f"Unexpected {name} notebook status: {status}")

    sagemaker_wait_stopped()


def get_notebook_instance_type():
    instance_type = boto_sagemaker().describe_notebook_instance(
        NotebookInstanceName=sagemaker_notebook_name()
    )["InstanceType"]
    return instance_type


def sagemaker_notebook_status(instance_name: Optional[str] = None) -> NotebookStatus:
    if instance_name is None:
        instance_name = sagemaker_notebook_name()

    status = boto_sagemaker().describe_notebook_instance(
        NotebookInstanceName=instance_name
    )["NotebookInstanceStatus"]
    return NotebookStatus(status)


def run(
    args: Sequence[str],
    cwd: Optional[str] = None,
    capture_output: bool = False,
    env: Optional[Mapping[str, str]] = None,
    input: Optional[str] = None,
) -> subprocess.CompletedProcess:
    if cwd is None:
        cwd = os.getcwd()

    print(f"Running in {cwd}: {args}")

    if env is None:
        sub_env = None
    else:
        sub_env = os.environ.copy()
        sub_env.update(env)

    return subprocess.run(
        args,
        cwd=cwd,
        capture_output=capture_output,
        env=sub_env,
        check=True,
        input=input,
    )


def read_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def sagemaker_up(instance_type="ml.t3.large", storage_gb=50):
    """
    Creates and starts the SageMaker notebook

    :param instance_type:
    :param storage_gb:
    :return:
    """

    s3_up()

    notebook_name = sagemaker_notebook_name()

    run(
        [
            "terragrunt",
            "apply",
            "-auto-approve"
        ],
        cwd=os.path.join(project_path, "dev", "aws-sagemaker"),
    )

    dynamodb_set_notebook_state(notebook_name, "creating")

    run(
        [
            "terragrunt",
            "apply",
            "-auto-approve",
            "-var",
            f"notebook_name={notebook_name}",
            "-var",
            f"instance_type={instance_type}",
            "-var",
            f"volume_size_gb={storage_gb}",
        ],
        cwd=os.path.join(project_path, "dev", "aws-sagemaker-notebook")
    )

    while dynamodb_get_notebook_state(notebook_name) != "installed":
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
    status = sagemaker_notebook_status()

    if status != NotebookStatus.Deleting:
        confirm = input(
            "Are files saved in the notebook will be lost when the notebook is deleted. Confirm [y/n]: "
        )
        if confirm != "y":
            return

        output = terraform_output("aws-sagemaker-notebook")

        run(
            [
                "terragrunt",
                "destroy",
                "-auto-approve",
                "-var",
                f"notebook_name={output['notebook_name']}",
            ],
            cwd=os.path.join(project_path, "dev", "aws-sagemaker-notebook")
        )

    # run(
    #     [
    #         "terragrunt",
    #         "destroy",
    #         "-auto-approve",
    #     ],
    #     cwd=os.path.join(project_path, "dev", "aws-sagemaker")
    # )


def sagemaker_wait_deleted():
    name = sagemaker_notebook_name()
    print(f"Waiting for {name} to be deleted (about 2 minutes)...")
    boto_sagemaker().get_waiter("notebook_instance_deleted").wait(
        NotebookInstanceName=name
    )


def terraform_output(module: str, env: Optional[dict] = None):
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


def aws_up(*, region: str = 'us-west-2'):
    """
    Configures the AWS account access

    :return:
    """

    opts = {}

    if 'PROJECT_USER' in os.environ:
        project_user = os.environ['PROJECT_USER']
        print(f"Detected project user name = {project_user}")
    else:
        project_user = input(f"Enter project user name: ")
        if re.match(r"^[a-z0-9\-]+$", project_user) is None:
            raise ValueError(
                "The project user name may only contain lowercase letters, numbers and dashes."
            )

    opts['PROJECT_USER'] = project_user

    opts.update({
        "AWS_ACCESS_KEY_ID": input("Enter AWS access key ID: "),
        "AWS_SECRET_ACCESS_KEY": input("Enter AWS secret access key: "),
        "AWS_SESSION_TOKEN": input("Enter AWS session token: "),
        "AWS_REGION": region
    })

    if opts['AWS_SESSION_TOKEN'] == "":
        del opts['AWS_SESSION_TOKEN']

    with open(os.path.join(project_path, "dev", "cli.env"), "w") as f:
        f.write("\n".join("=".join(p) for p in opts.items()))

    load_env()
    #s3_up()


def s3_up():
    """
    Creates an S3 bucket for infrastructure information

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
        env={"AWS_REGION": s3_bucket_region()}
    )


def aws_down():
    """
    Removes the S3 bucket with infrastructure description

    :return:
    """

    bucket = boto_session().resource("s3").Bucket(s3_bucket_name())
    bucket.objects.all().delete()

    run(
        [
            "terragrunt",
            "destroy",
            "-auto-approve",
            "-var",
            f"s3_bucket_name={s3_bucket_name()}",
        ],
        cwd=os.path.join(project_path, "dev", "aws-s3"),
        env={"AWS_REGION": s3_bucket_region()}
    )

    boto_session().resource("dynamodb", region_name=s3_bucket_region()).Table(
        "ucla-deeplearning-terraform-lock"
    ).delete()


def terraform_output_sagemaker():
    return terraform_output(
        "aws-sagemaker",
    )


def terraform_output_ec2():
    return terraform_output("aws-ec2", env={"s3_bucket_name": s3_bucket_name()})


def dynamodb_set_notebook_state(name: str, state: str):
    db = boto_session().client("dynamodb")
    db.put_item(
        TableName=terraform_output_sagemaker()["dynamodb_table_name"],
        Item={"name": {"S": name}, "state": {"S": state}},
    )


def ec2_up(*, instance_type: str = "t2.xlarge", storage_gb: int = 50):
    """
    Creates and starts the EC2 instance, then install the system packages (e.g. Docker).

    """
    key_path = f"{project_path}/dev/aws-ec2/key"
    if not os.path.exists(key_path):
        run(["ssh-keygen", "-f", key_path, "-N", "", "-q"])

    bucket_name = s3_bucket_name()

    run(
        [
            "terragrunt",
            "apply",
            "-auto-approve",
            "-var",
            f"instance_type={instance_type}",
            "-var",
            f"storage_gb={storage_gb}"
        ],
        cwd=os.path.join(project_path, "dev", "aws-ec2"),
        env={"s3_bucket_name": bucket_name},
    )

    print("Waiting for the EC2 instance to boot...")
    sleep(60)

    ec2_install()
    print("Ready")


def ec2_install():
    """
    Installs the Docker and Github repo on the EC2 instance.
    """
    ec2_ssh(stdin=read_bytes(f"{project_path}/dev/aws-ec2/install_docker.sh"))
    ec2_ssh(stdin=read_bytes(f"{project_path}/dev/aws-ec2/clone_repo.sh"))


def ec2_down():
    """
    Stops and removes the EC2 instance

    """
    bucket_name = s3_bucket_name()

    run(
        ["terragrunt", "destroy", "-auto-approve", "-var", "instance_type=t2.xlarge", "-var", "storage_gb=50"],
        cwd=os.path.join(project_path, "dev", "aws-ec2"),
        env={"s3_bucket_name": bucket_name},
    )


def ec2_ssh(*cmd: str, stdin=None):
    """
    Connects to the running EC2 instance via SSH

    :param cmd:
    :param stdin:
    :return:
    """

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
    key_path = f"{project_path}/dev/aws-ec2/key"
    username = connection["username"]

    args = [
        "ssh",
        "-i",
        key_path,
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        f"{username}@{ip}",
        *cmd,
    ]

    print(f"Running {args}")
    run(args, input=None if stdin is None else stdin.decode())


def ec2_tunnel(*cmd):
    """
    Starts a tunnel to the running EC2 instance (to access Docker and Jupyter).

    If required, also starts the EC2 instance.
    :param cmd:
    :return:
    """
    local_docker_path = f"{project_path}/dev/aws-ec2/docker.sock"

    ec2_start()

    ssh_cmd = [
        "-L",
        f"{local_docker_path}:/var/run/docker.sock",
        "-L",
        "0.0.0.0:5000:localhost:3000",
        *cmd,
    ]

    subprocess.run(["rm", "-f", local_docker_path])
    ec2_ssh(*ssh_cmd)
    subprocess.run(["rm", "-f", local_docker_path])


def ec2_start():
    """
    Starts the previously created EC2 instance

    :return:
    """
    instance_id = terraform_output_ec2()["ec2"]["instance_id"]

    boto_session().client("ec2").start_instances(InstanceIds=[instance_id])
    ec2_wait_started(instance_id)


def ec2_wait_started(instance_id: str):
    print("Waiting to be running...")
    waiter = boto_session().client("ec2").get_waiter("instance_running")
    waiter.wait(InstanceIds=[instance_id])
    print("Running")


def ec2_stop():
    """
    Stops the running EC2 instance
    """
    instance_id = terraform_output_ec2()["ec2"]["instance_id"]

    ec2 = boto_session().client("ec2")
    ec2.stop_instances(InstanceIds=[instance_id])

    print("Waiting to stop...")
    waiter = ec2.get_waiter("instance_stopped")
    waiter.wait(InstanceIds=[instance_id])
    print("Stopped")


def ec2_resize(instance_size: str):
    """
    Resizes the instance and restarts it

    :param instance_size:
    :return:
    """
    instance_id = terraform_output_ec2()["ec2"]["instance_id"]

    ec2_stop()
    ec2 = boto_session().client("ec2")
    ec2.modify_instance_attribute(
        InstanceId=instance_id, Attribute="instanceType", Value=instance_size
    )
    ec2_start()


def ec2_nvidia():
    """
    Installs the NVidia drivers on the running EC2 instance

    :return:
    """
    ec2_ssh(stdin=read_bytes(f"{project_path}/dev/aws-ec2/install_nvidia.sh"))


def dynamodb_get_notebook_state(name: str):
    db = boto_session().client("dynamodb")
    response = db.get_item(
        TableName=terraform_output_sagemaker()["dynamodb_table_name"],
        Key={"name": {"S": name}},
        ConsistentRead=True,
    )

    return response["Item"]["state"]["S"]


def gpg_decrypt(data: bytes, passphrase: str) -> bytes:
    with tempfile.NamedTemporaryFile() as enc:
        enc.write(data)
        enc.flush()

        with subprocess.Popen(
            ['gpg', '--batch', '--pinentry-mode', 'loopback', '--passphrase-fd', '0', '--decrypt', enc.name],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as p:
            out, err = p.communicate(passphrase.encode())
            if p.returncode != 0:
                print(err)
                raise Exception(f'GPG returned non-zero code')

    return out


def iam_team():
    passphrase = input('Enter GPG key passphrase: ')
    for name, user in terraform_output('aws-iam-team')['users'].items():
        aws_login_password = user['aws_login_password']
        aws_login_password = b64decode(aws_login_password)
        aws_login_password = gpg_decrypt(aws_login_password, passphrase).decode()
        print(f'Username: {name} / Password: {aws_login_password}')


def aws_cli(*cmd):
    run(['aws', *cmd])


def terragrunt(module, *cmd):
    run(
        ['terragrunt', *cmd],
        cwd=f'{project_path}/dev/{module}',
    )

if __name__ == "__main__":
    load_env()
    clize.run(
        [
            # Local
            jupyter_up,
            jupyter_start,
            jupyter_stop,
            jupyter_down,
            jupyter_pull,
            shell,

            # AWS Common
            aws_up,
            aws_down,

            # AWS EC2
            ec2_up,
            ec2_start,
            ec2_tunnel,
            ec2_resize,
            ec2_nvidia,
            ec2_stop,
            ec2_down,
            ec2_ssh,
            ec2_install,

            # AWS team admin
            iam_team,
            sagemaker_team_start,
            sagemaker_team_stop,

            # AWS SageMaker team member
            sagemaker_start,
            sagemaker_resize,
            sagemaker_stop,

            # Internal
            docker_cli,
            jupyter_build,
            aws_cli,

            # Terraform
            s3_up,
            terragrunt,
            terraform_output_sagemaker,
            terraform_output_ec2,

            # AWS SageMaker independent
            sagemaker_up,
            sagemaker_down,
        ]
    )
