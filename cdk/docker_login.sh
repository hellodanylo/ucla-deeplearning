#!/usr/bin/env zsh

set -eux

aws --region $AWS_REGION ecr get-login-password | docker login --username AWS --password-stdin $COLLEGIUM_ECR
