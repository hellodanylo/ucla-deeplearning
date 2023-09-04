#!/usr/bin/env zsh
set -eux

mkdir -p /home/sagemaker-user/mlflow
ln -s /home/sagemaker-user/mlflow /app/mlflow
echo "Revision {revision}" /app/studio_kernel_lifecycle
