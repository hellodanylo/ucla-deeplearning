#!/usr/bin/env zsh

set -eux

if [[ $BUILD_STAGE == "docker" ]];
then
    cdk/docker_build.sh
    cdk/docker_push.sh
fi

if [[ $BUILD_STAGE == "test" ]];
then
    cdk/test.sh
fi

if [[ $BUILD_STAGE == "cdk" ]];
then
    cdk/cdk_deploy.sh
fi