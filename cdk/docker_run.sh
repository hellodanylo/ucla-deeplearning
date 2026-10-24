#!/usr/bin/env zsh

# Interactive shell in the Studio image with the working tree mounted

project_path=${0:a:h:h}
source $project_path/cdk/env.sh

docker run \
    --rm \
    -v $project_path:/app/collegium \
    --name collegium \
    --hostname collegium \
    -it \
    $COLLEGIUM_ECR:$CODEBUILD_RESOLVED_SOURCE_VERSION \
    $*
