#!/usr/bin/env zsh

export project_path=${0:a:h:h}
pushd $project_path

conda activate collegium 2>/dev/null || true

set -a;
source $project_path/cdk/.env || true
set +a;

app_vars=$(aws --region $AWS_REGION ssm get-parameter --name /collegium/app-resources | jq -r .Parameter.Value)
build_vars=$(aws --region $AWS_REGION ssm get-parameter --name /collegium/build-resources | jq -r .Parameter.Value)

export COLLEGIUM_ECR=$(echo $build_vars | jq -r .collegiumEcr)
export DOCTRINA_ECR=$(echo $app_vars | jq -r .doctrina_ecr)
export CODEBUILD_RESOLVED_SOURCE_VERSION=${CODEBUILD_RESOLVED_SOURCE_VERSION:-$(git rev-parse HEAD)}

popd
