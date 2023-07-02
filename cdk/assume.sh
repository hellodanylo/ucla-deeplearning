#!/usr/bin/env zsh

ACCOUNT_ID=$(aws sts get-caller-identity | jq -r '.Account')
ASSUME_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/collegium-codebuild"

# Get temporary credentials from STS
TEMP_ROLE=$(aws sts assume-role --role-arn $ASSUME_ROLE_ARN --role-session-name cdk-assume)

export AWS_ACCESS_KEY_ID=$(echo "${TEMP_ROLE}" | jq -r '.Credentials.AccessKeyId')
export AWS_SECRET_ACCESS_KEY=$(echo "${TEMP_ROLE}" | jq -r '.Credentials.SecretAccessKey')
export AWS_SESSION_TOKEN=$(echo "${TEMP_ROLE}" | jq -r '.Credentials.SessionToken')