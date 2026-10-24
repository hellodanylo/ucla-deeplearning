#!/usr/bin/env zsh

set -eux

for repo in "$COLLEGIUM_ECR" "$COLLEGIUM_CDK_ECR"; do
    docker push "${repo}:${CODEBUILD_RESOLVED_SOURCE_VERSION}"
    docker push "${repo}:latest"
done
