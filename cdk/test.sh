#!/usr/bin/env zsh

set -eux

versioned_uri="${COLLEGIUM_ECR}:${CODEBUILD_RESOLVED_SOURCE_VERSION}"

aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $COLLEGIUM_ECR

docker pull "$versioned_uri"

docker run --rm "$versioned_uri" python -m unittest