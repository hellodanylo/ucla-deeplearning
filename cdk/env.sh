#!/usr/bin/env zsh

export project_path=${0:a:h:h}
pushd $project_path

set -a;
source $project_path/cdk/.env || true
set +a;

build_vars=$(aws --region $AWS_REGION ssm get-parameter --name /collegium/build-resources | jq -r .Parameter.Value)

export COLLEGIUM_ECR=$(echo $build_vars | jq -r .collegiumEcr)
export COLLEGIUM_CDK_ECR=$(echo $build_vars | jq -r .collegiumCdkEcr)
export CODEBUILD_RESOLVED_SOURCE_VERSION=${CODEBUILD_RESOLVED_SOURCE_VERSION:-$(git rev-parse HEAD)}
export STUDIO_IMAGE_TAG=${STUDIO_IMAGE_TAG:-env-$(git rev-parse HEAD:cdk/docker-studio | cut -c1-12)}
export CDK_IMAGE_TAG=${CDK_IMAGE_TAG:-src-$(git rev-parse HEAD:cdk HEAD:pyproject.toml | git hash-object --stdin | cut -c1-12)}

popd
