# %%
import boto3

# %%
import os

from collegium.cdk.environment import SSMParameter
from collegium.cdk.team_stack import TeamConfig
s = boto3.Session(region_name=os.environ.get('AWS_REGION'))
ec2 = s.client('ec2')

# %%
usage_lines = []

# %%
import pprint
import datetime as dt
for res in ec2.describe_instances()['Reservations']:
    for instance in res['Instances']:
        if instance['State']['Name'] != 'running':
            continue
        timestamp = instance['UsageOperationUpdateTime']
        duration_hours = round((dt.datetime.now().astimezone() - timestamp).seconds / 60 / 60, 2)
        usage_lines.append({
            'user': '',
            'resource': 'ec2',
            'instance_type': instance['InstanceType'],
            'duration_hours': duration_hours,
        })
        
usage_lines

# %%
sm = s.client('sagemaker')
for app in sm.list_apps()['Apps']:
    if app['AppType'] != 'KernelGateway' or app['Status'] != 'InService':
        continue
    timestamp = app['CreationTime']
    duration_hours = round((dt.datetime.now().astimezone() - timestamp).seconds / 60 / 60, 2)
    usage_lines.append({
        'resource': 'sagemaker_kernel',
        'instance_type': app['ResourceSpec']['InstanceType'],
        'user': app['UserProfileName'],
        'duration_hours': duration_hours,
    })

# %%
import pandas as pd
import polars as pl
df = pl.from_dicts(usage_lines).sort('*')
html = df.to_pandas().to_html()
print(df)

# %%
ssm = s.client('ssm')
config_json = ssm.get_parameter(Name=SSMParameter.TEAM_CONFIG.value)['Parameter']['Value']
team_config = TeamConfig.from_json(config_json)

# %%
ses = s.client('ses')
ses.send_email(
    Source=os.environ['AWS_SES_SOURCE'],
    Destination={'ToAddresses': [team_config.admin.email]},
    Message={
        'Subject': {'Data': 'Collegium - Live Usage Report'},
        'Body': {
            'Html': {'Data': html},
        }
    },
)


