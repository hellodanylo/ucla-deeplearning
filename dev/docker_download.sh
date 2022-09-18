#!/usr/bin/env zsh

docker_host=$1
image_name=$2

docker -H $docker_host image save $image_name | docker image load