#!/usr/bin/env zsh

set -eux

latest_uri="${COLLEGIUM_ECR}:latest"
versioned_uri="${COLLEGIUM_ECR}:${CODEBUILD_RESOLVED_SOURCE_VERSION}"

docker push "$versioned_uri"
docker tag "$versioned_uri" "$latest_uri"
docker push "$latest_uri"
