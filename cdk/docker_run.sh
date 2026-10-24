#!/usr/bin/env zsh

# Interactive shell in the Studio image with the working tree mounted as the course checkout

project_path=${0:a:h:h}
source $project_path/cdk/env.sh

docker run \
    --rm \
    -v $project_path:/home/sagemaker-user/collegium \
    --name collegium \
    --hostname collegium \
    -it \
    "${COLLEGIUM_ECR}:${STUDIO_IMAGE_TAG}" \
    $*
