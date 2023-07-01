#!/usr/bin/env zsh

set -eux

project_path=${0:h:h}
latest_uri="${COLLEGIUM_ECR}:latest"
versioned_uri="${COLLEGIUM_ECR}:${CODEBUILD_RESOLVED_SOURCE_VERSION}"

aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $COLLEGIUM_ECR

docker version
docker build \
    --cache-from "$latest_uri" \
    --build-arg "BASE_IMAGE=${DOCTRINA_ECR}:base-latest" \
    --build-arg "CONDA_ENV=conda_lock.yml" \
    --build-arg "BUILDKIT_INLINE_CACHE=1" \
    --tag "$versioned_uri" \
    "$project_path"
