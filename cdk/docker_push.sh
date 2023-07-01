#!/usr/bin/env zsh

set -eux

latest_uri="${COLLEGIUM_ECR}:latest"
versioned_uri="${COLLEGIUM_ECR}:${CODEBUILD_RESOLVED_SOURCE_VERSION}"

docker push "$latest_uri"
docker tag "$latest_uri" "$versioned_uri"
docker push "$versioned_uri"
