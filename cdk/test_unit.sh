#!/usr/bin/env zsh

set -eux

versioned_uri="${COLLEGIUM_ECR}:${CODEBUILD_RESOLVED_SOURCE_VERSION}"

docker run --rm "$versioned_uri" \
    python -m unittest

