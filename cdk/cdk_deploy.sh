#!/usr/bin/env zsh

set -eux

project_path="${0:a:h:h}"

# Import the temporary credentials
set +x;
source $project_path/cdk/assume.sh
set -x;

# either cdk runs interactively or
# security changes must be pre-approved

docker run \
    -e AWS_ACCESS_KEY_ID \
    -e AWS_SECRET_ACCESS_KEY \
    -e AWS_SESSION_TOKEN \
    -e AWS_REGION \
    -e AWS_DEFAULT_REGION=$AWS_REGION \
    -e STUDIO_IMAGE_TAG \
    --rm \
    -it \
    "${COLLEGIUM_CDK_ECR}:${CDK_IMAGE_TAG}" \
    cdk deploy --all
