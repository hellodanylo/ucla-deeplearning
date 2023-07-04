#!/usr/bin/env python3

import os

workspace = '/storage/mnist/jobs'

s3_path = f's3://white-data-ml-live-private{workspace}'
os.system(f'aws s3 sync {s3_path} {workspace}')