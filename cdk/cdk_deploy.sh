#!/usr/bin/env zsh

set -eux

versioned_uri="${COLLEGIUM_ECR}:${CODEBUILD_RESOLVED_SOURCE_VERSION}"
docker run --rm -w /app/collegium/cdk "$versioned_uri" npx cdk deploy --all