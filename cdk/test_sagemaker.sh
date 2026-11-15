#!/usr/bin/env zsh

set -eux

project_path=${0:a:h:h}

# Credentials for the launcher container. It waits for the notebook job, which can take longer
# than the 1 h limit of an assumed (chained) role session, so in CodeBuild pass the build's
# container credentials endpoint instead: botocore refreshes those automatically.
if [[ -n "${AWS_CONTAINER_CREDENTIALS_RELATIVE_URI:-}" ]]; then
    credential_env=(-e AWS_CONTAINER_CREDENTIALS_RELATIVE_URI)
else
    set +x
    source $project_path/cdk/assume.sh
    set -x
    credential_env=(-e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN)
fi

# The launcher runs in the CDK image; the training job fetches this commit from GitHub and
# executes its notebooks in the Studio image
docker run \
    "${credential_env[@]}" \
    -e AWS_REGION \
    -e AWS_DEFAULT_REGION=$AWS_REGION \
    --rm "${COLLEGIUM_CDK_ECR}:${CDK_IMAGE_TAG}" \
    python -m collegium.cdk.cli sagemaker-jupyter-process --image-version "${STUDIO_IMAGE_TAG}" \
    --git-commit "${CODEBUILD_RESOLVED_SOURCE_VERSION}" --test-key "${NOTEBOOK_TEST_KEY}"
