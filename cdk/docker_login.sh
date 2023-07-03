#!/usr/bin/env zsh

aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $COLLEGIUM_ECR