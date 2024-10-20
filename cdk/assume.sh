#!/usr/bin/env zsh

role=${1:-collegium-codebuild}

unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY
unset AWS_SESSION_TOKEN
ACCOUNT_ID=$(aws sts get-caller-identity | jq -r '.Account')
ASSUME_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${role}"

# Get temporary credentials from STS
TEMP_ROLE=$(aws sts assume-role --role-arn $ASSUME_ROLE_ARN --role-session-name cdk-assume)
export AWS_ACCESS_KEY_ID=$(echo "${TEMP_ROLE}" | jq -r '.Credentials.AccessKeyId')
export AWS_SECRET_ACCESS_KEY=$(echo "${TEMP_ROLE}" | jq -r '.Credentials.SecretAccessKey')
export AWS_SESSION_TOKEN=$(echo "${TEMP_ROLE}" | jq -r '.Credentials.SessionToken')