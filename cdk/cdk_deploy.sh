#!/usr/bin/env zsh

set -eux

docker run --rm -w /app/collegium/cdk -it "${COLLEGIUM_ECR}:latest" npx cdk deploy --all