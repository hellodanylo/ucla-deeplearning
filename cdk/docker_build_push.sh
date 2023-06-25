#!/usr/bin/env zsh

set -eux

aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO

docker build \
    --build-arg "BASE_IMAGE=${DOCTRINA_REPO}:base-latest" \
    --tag "${ECR_REPO}:latest" \
    dev/docker-jupyter

docker push "${ECR_REPO}:latest"
