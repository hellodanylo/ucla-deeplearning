#!/usr/bin/env zsh

set -eux

cdk/docker_build.sh
cdk/test.sh
cdk/docker_push.sh
cdk/cdk_deploy.sh