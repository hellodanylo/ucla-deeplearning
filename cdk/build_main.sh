#!/usr/bin/env zsh

set -eux

cdk/docker_login.sh
cdk/docker_build.sh
cdk/test_unit.sh
cdk/docker_push.sh
cdk/test_sagemaker.sh
cdk/cdk_deploy.sh