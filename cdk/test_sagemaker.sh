#!/usr/bin/env zsh

set -eux

project_path=${0:a:h:h}

# Import the temporary credentials
set +x
source $project_path/cdk/assume.sh
set -x

# The launcher runs in the CDK image; the training job executes the notebooks in the Studio image
docker run \
    -e AWS_ACCESS_KEY_ID \
    -e AWS_SECRET_ACCESS_KEY \
    -e AWS_SESSION_TOKEN \
    -e AWS_REGION \
    -e AWS_DEFAULT_REGION=$AWS_REGION \
    --rm "${COLLEGIUM_CDK_ECR}:${CODEBUILD_RESOLVED_SOURCE_VERSION}" \
    python -m collegium.cdk.cli sagemaker-jupyter-process --image-version "${CODEBUILD_RESOLVED_SOURCE_VERSION}"
