#!/usr/bin/env zsh

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
