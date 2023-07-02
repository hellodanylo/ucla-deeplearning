#!/usr/bin/env zsh

set -eux

project_path="${0:a:h:h}"

versioned_uri="${COLLEGIUM_ECR}:${CODEBUILD_RESOLVED_SOURCE_VERSION}"

aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $COLLEGIUM_ECR

# Import the temporary credentials
source $project_path/cdk/assume.sh

docker run \
    -e AWS_ACCESS_KEY_ID \
    -e AWS_SECRET_ACCESS_KEY \
    -e AWS_SESSION_TOKEN \
    -e AWS_REGION \
    --rm -w /app/collegium/cdk \
    "$versioned_uri" \
    npx cdk deploy --all
