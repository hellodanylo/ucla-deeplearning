#!/usr/bin/env

project_path=${0:a:h:h}

conda activate collegium || true

set -a;
source $project_path/cdk/.env
set +a;

export CODEBUILD_RESOLVED_SOURCE_VERSION=$(git rev-parse HEAD)
