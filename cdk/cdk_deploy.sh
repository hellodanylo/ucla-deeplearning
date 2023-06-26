#!/usr/bin/env zsh

set -eux

npm install -g aws-cdk
pip install aws-cdk-lib

cd cdk && npx cdk deploy --all