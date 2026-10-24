#!/usr/bin/env zsh

set -eux

project_path=${0:a:h:h}

# The Studio image has no course code: mount the checkout where the image resolves `collegium.*` imports
docker run --rm \
    -v $project_path:/home/sagemaker-user/collegium:ro \
    "${COLLEGIUM_ECR}:${STUDIO_IMAGE_TAG}" \
    pytest -p no:cacheprovider /home/sagemaker-user/collegium/test
