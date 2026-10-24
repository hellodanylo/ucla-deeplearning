#!/usr/bin/env zsh

set -eux

project_path=${0:a:h:h}

export DOCKER_BUILDKIT=1
docker version

# build <ecr-repo-uri> <dockerfile>: tags :<commit> and :latest, using :latest as the layer cache
build() {
    docker buildx build \
        --cache-from="${1}:latest" \
        --cache-to="type=inline" \
        --tag "${1}:${CODEBUILD_RESOLVED_SOURCE_VERSION}" \
        -f "$2" \
        "$project_path"
    docker tag "${1}:${CODEBUILD_RESOLVED_SOURCE_VERSION}" "${1}:latest"
}

# SageMaker Studio image: domain, unit tests, notebook tests
build "$COLLEGIUM_ECR" $project_path/cdk/docker-studio/Dockerfile
# Deployment tooling image: cdk deploy, SageMaker job launcher
build "$COLLEGIUM_CDK_ECR" $project_path/cdk/docker-cdk/Dockerfile
