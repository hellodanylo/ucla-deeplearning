#!/usr/bin/env zsh

set -eux

project_path=${0:a:h:h}

export DOCKER_BUILDKIT=1
docker version

# build_or_pull <ecr-repo-uri> <tag> <dockerfile> <context>
# Tags are derived from the image's source content, so an existing tag is pulled instead of rebuilt.
# Either way the image is also tagged :latest, which is the layer cache for future builds.
build_or_pull() {
    if docker manifest inspect "${1}:${2}" >/dev/null 2>&1; then
        docker pull "${1}:${2}"
    else
        docker buildx build \
            --cache-from="${1}:latest" \
            --cache-to="type=inline" \
            --tag "${1}:${2}" \
            -f "$3" \
            "$4"
    fi
    docker tag "${1}:${2}" "${1}:latest"
}

# SageMaker Studio image: domain, unit tests, notebook tests
build_or_pull "$COLLEGIUM_ECR" "$STUDIO_IMAGE_TAG" $project_path/cdk/docker-studio/Dockerfile $project_path/cdk/docker-studio

# Deployment tooling image: cdk deploy, SageMaker job launcher
build_or_pull "$COLLEGIUM_CDK_ECR" "$CDK_IMAGE_TAG" $project_path/cdk/docker-cdk/Dockerfile "$project_path"
