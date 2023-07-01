import boto3
import os
from typing import Optional


sagemaker_client = boto3.client("sagemaker")
studio_lifecycle_config_content = os.environ.get("studio_lifecycle_config_content")
studio_lifecycle_config_name = os.environ.get("studio_lifecycle_config_name")
studio_lifecycle_config_app_type = os.environ.get("studio_lifecycle_config_app_type")


def handler(event, context):
    request_type = event["RequestType"]
    if request_type == "Create":
        return on_create()
    if request_type == "Update":
        raise Exception(
            "A Lifecycle Configuration script cannot be changed after it has been created. To update your script, you must create a new Lifecycle Configuration script."
        )
    if request_type == "Delete":
        return on_delete()
    raise Exception("Invalid request type: {}".format(request_type))


def on_create():
    assert studio_lifecycle_config_name is not None
    assert studio_lifecycle_config_app_type is not None

    studio_lifecycle_config_arn = create_studio_lifecycle_configuration(
        studio_lifecycle_config_content=studio_lifecycle_config_content,
        studio_lifecycle_config_name=studio_lifecycle_config_name,
        studio_lifecycle_config_app_type=studio_lifecycle_config_app_type,
    )
    output = {
        "PhysicalResourceId": studio_lifecycle_config_name,
        "Data": {"StudioLifecycleConfigArn": studio_lifecycle_config_arn},
    }
    return output


def on_delete():
    delete_studio_lifecycle_configuration(
        studio_lifecycle_config_name=studio_lifecycle_config_name
    )


def create_studio_lifecycle_configuration(
    studio_lifecycle_config_content,
    studio_lifecycle_config_name: str,
    studio_lifecycle_config_app_type: str,
):

    response = sagemaker_client.create_studio_lifecycle_config(
        StudioLifecycleConfigName=studio_lifecycle_config_name,
        StudioLifecycleConfigContent=studio_lifecycle_config_content,
        StudioLifecycleConfigAppType=studio_lifecycle_config_app_type,
    )

    return response["StudioLifecycleConfigArn"]


def delete_studio_lifecycle_configuration(
    studio_lifecycle_config_name,
):
    sagemaker_client.delete_studio_lifecycle_config(
        StudioLifecycleConfigName=studio_lifecycle_config_name
    )