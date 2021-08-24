import os
from typing import Dict, Any

import boto3


def handle(payload: Dict, context: Any):
    print(payload)
    for record in payload["Records"]:
        notification = record['Sns']
        handle_message(notification['Message'])


def handle_budget(user_name: str):
    sm = boto3.Session(region_name=os.environ.get('AWS_REGION')).client('sagemaker')

    instance_name = f'ucla-deeplearning-{user_name}'
    status = sm.describe_notebook_instance(
        NotebookInstanceName=instance_name
    )["NotebookInstanceStatus"]

    if status == 'InService':
        print(f'Will stop {instance_name}')
        sm.stop_notebook_instance(NotebookInstanceName=instance_name)
    else:
        print(f'Will skip {instance_name} due to being stopped')


def handle_message(message: str):
    for line in message.split('\n'):
        parts = line.split(': ')
        if len(parts) == 2 and parts[0] == 'Budget Name':
            user_name = '-'.join(parts[1].split('-')[:-1])
            handle_budget(user_name)
            return user_name
