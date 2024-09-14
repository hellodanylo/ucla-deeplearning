import json
import boto3
import datetime as dt
import os

# Dependencies:
# 1. AWS credentials
# 2. SSM Parameter - TeamConfig
# 3. SSM Parameter - CoreResources
# 4. Environment - AWS_REGION

s = boto3.Session(region_name=os.environ.get('AWS_REGION'))

def report_live_usage():
    usage_lines = build_ec2_usage_lines() + build_sagemaker_usage_lines()
    if len(usage_lines) == 0:
        return

    usage_lines.sort(key=lambda x: tuple(x.values()))
    html_body = format_usage_lines(usage_lines)
    send_email(html_body)


def build_ec2_usage_lines():
    ec2 = s.client('ec2')
    usage_lines = []
    for res in ec2.describe_instances()['Reservations']:
        for instance in res['Instances']:
            if instance['State']['Name'] != 'running':
                continue
            timestamp = instance['LaunchTime']
            duration_hours = round((dt.datetime.now().astimezone() - timestamp).seconds / 60 / 60, 2)
            usage_lines.append({
                'user': '',
                'resource': 'ec2',
                'instance_type': instance['InstanceType'],
                'duration_hours': duration_hours,
            })

    return usage_lines
        
def build_sagemaker_usage_lines():
    sm = s.client('sagemaker')
    usage_lines = []
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
    return usage_lines


def format_usage_lines(usage_lines):
    html_rows = '<tbody>' + ''.join([
        '<tr>' + ''.join(f'<td>{val}</td>' for val in row.values()) + '</tr>'
        for row in usage_lines
    ]) + '</tbody>'
    header = '<thead>' + ''.join(f'<th>{key}</th>' for key in usage_lines[0].keys()) + '</thead>'
    html_body = f'<table>{header}{html_rows}</table>'
    return html_body


def send_email(html_body):
    ssm = s.client('ssm')
    team_config = json.loads(ssm.get_parameter(Name='/collegium/team-config')['Parameter']['Value'])
    app_resources = json.loads(ssm.get_parameter(Name='/collegium/app-resources')['Parameter']['Value'])

    ses = s.client('ses')
    ses.send_email(
        Source=app_resources['ses_source'],
        Destination={'ToAddresses': [team_config['admin']['email']]},
        Message={
            'Subject': {'Data': 'Collegium - Live Usage Report'},
            'Body': {
                'Html': {'Data': html_body},
            }
        },
    )


def lambda_handler(event, context):
    report_live_usage()


if __name__ == '__main__':
    report_live_usage()
