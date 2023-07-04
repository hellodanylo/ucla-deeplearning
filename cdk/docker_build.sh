#!/usr/bin/env zsh

set -eux

project_path=${0:h:h}
latest_uri="${COLLEGIUM_ECR}:latest"
versioned_uri="${COLLEGIUM_ECR}:${CODEBUILD_RESOLVED_SOURCE_VERSION}"

export DOCKER_BUILDKIT=1
docker version
docker buildx build \
    --cache-from="$latest_uri" \
    --cache-to="type=inline" \
    --build-arg "BASE_IMAGE=${DOCTRINA_ECR}:base-latest" \
    --build-arg "CONDA_ENV=conda_init.yml" \
    --tag "$versioned_uri" \
    "$project_path"
