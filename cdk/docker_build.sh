#!/usr/bin/env zsh

set -eux

project_path=${0:h:h}

aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $COLLEGIUM_ECR

docker build \
    --cache-from "${COLLEGIUM_ECR}:latest" \
    --build-arg "BASE_IMAGE=${DOCTRINA_ECR}:base-latest" \
    --build-arg "CONDA_ENV=conda_lock.yml" \
    --build-arg "BUILDKIT_INLINE_CACHE=1" \
    --tag "${COLLEGIUM_ECR}:latest" \
    "$project_path"
