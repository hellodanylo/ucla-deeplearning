#!/usr/bin/env zsh

set -eux

project_path=${0:a:h:h}

$project_path/cdk/docker_login.sh
$project_path/cdk/docker_build.sh
$project_path/cdk/test_unit.sh
$project_path/cdk/docker_push.sh
$project_path/cdk/test_sagemaker.sh
# $project_path/cdk/cdk_deploy.sh
