from typing import Dict


def handle(payload: Dict, context):
    print(payload)
    for record in payload["Records"]:
        notification = record['Sns']
        print(f"{notification['Subject']} = {notification['Message']}")
