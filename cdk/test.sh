#!/usr/bin/env zsh

set -eux

versioned_uri="${COLLEGIUM_ECR}:${CODEBUILD_RESOLVED_SOURCE_VERSION}"

aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $COLLEGIUM_ECR

docker run --rm "$versioned_uri" \
    python -m unittest

docker run --rm "$versioned_uri" \
    python \
    /app/collegium/foundation/jupyter_render.py \
    process 01_dnn 02_cnn 03_rnn 04_gan 05_ensemble \
    --execute