#!/usr/bin/env zsh

set -eux

project_path=${0:a:h:h}

export DOCKER_BUILDKIT=1
docker version

# build <ecr-repo-uri> <tag> <dockerfile> <context>: tags :<tag> and :latest, using :latest as the layer cache
build() {
    docker buildx build \
        --cache-from="${1}:latest" \
        --cache-to="type=inline" \
        --tag "${1}:${2}" \
        -f "$3" \
        "$4"
    docker tag "${1}:${2}" "${1}:latest"
}

# SageMaker Studio image: domain, unit tests, notebook tests.
# Tagged by the content of cdk/docker-studio, so it is only rebuilt when the environment changes.
if docker manifest inspect "${COLLEGIUM_ECR}:${STUDIO_IMAGE_TAG}" >/dev/null 2>&1; then
    docker pull "${COLLEGIUM_ECR}:${STUDIO_IMAGE_TAG}"
    docker tag "${COLLEGIUM_ECR}:${STUDIO_IMAGE_TAG}" "${COLLEGIUM_ECR}:latest"
else
    build "$COLLEGIUM_ECR" "$STUDIO_IMAGE_TAG" $project_path/cdk/docker-studio/Dockerfile $project_path/cdk/docker-studio
fi

# Deployment tooling image: cdk deploy, SageMaker job launcher (contains the repo, so tagged by commit)
build "$COLLEGIUM_CDK_ECR" "$CODEBUILD_RESOLVED_SOURCE_VERSION" $project_path/cdk/docker-cdk/Dockerfile "$project_path"
