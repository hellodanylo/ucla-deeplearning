#!/usr/bin/env zsh

set -eux

# Pushing an existing tag again only re-uploads missing layers (none, if the build step pulled it)
docker push "${COLLEGIUM_ECR}:${STUDIO_IMAGE_TAG}"
docker push "${COLLEGIUM_ECR}:latest"
docker push "${COLLEGIUM_CDK_ECR}:${CODEBUILD_RESOLVED_SOURCE_VERSION}"
docker push "${COLLEGIUM_CDK_ECR}:latest"
