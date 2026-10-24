#!/usr/bin/env zsh

set -eux

project_path=${0:a:h:h}

# Image tags from the content they are built from, so unchanged images are pulled instead of rebuilt.
# Studio: git tree hash of cdk/docker-studio (same formula as get_studio_image_tag in cdk/app.py).
export STUDIO_IMAGE_TAG=env-$(git -C $project_path rev-parse HEAD:cdk/docker-studio | cut -c1-12)
# Tooling: git tree hash of cdk/ plus the root pyproject.toml blob (everything the image copies)
export CDK_IMAGE_TAG=src-$(git -C $project_path rev-parse HEAD:cdk HEAD:pyproject.toml | git hash-object --stdin | cut -c1-12)

$project_path/cdk/docker_login.sh
$project_path/cdk/docker_build.sh
$project_path/cdk/test_unit.sh
$project_path/cdk/docker_push.sh
$project_path/cdk/test_sagemaker.sh
# $project_path/cdk/cdk_deploy.sh
