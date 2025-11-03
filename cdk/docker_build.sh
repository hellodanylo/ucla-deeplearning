#!/usr/bin/env zsh

set -eux

project_path=${0:a:h:h}
latest_uri="${COLLEGIUM_ECR}:latest"
versioned_uri="${COLLEGIUM_ECR}:${CODEBUILD_RESOLVED_SOURCE_VERSION}"
conda_env=${CONDA_ENV:-conda_lock.yml}

export DOCKER_BUILDKIT=1
docker version
docker buildx build \
    --cache-from="$latest_uri" \
    --cache-to="type=inline" \
    --build-arg "BASE_IMAGE=public.ecr.aws/sagemaker/sagemaker-distribution:3.5.0-gpu" \
    --build-arg "CONDA_ENV=${conda_env}" \
    --tag "$versioned_uri" \
    -f $project_path/cdk/docker-jupyter/Dockerfile \
    "$project_path"

docker tag "$versioned_uri" "$latest_uri"
