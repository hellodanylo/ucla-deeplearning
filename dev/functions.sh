#!/usr/bin/env bash

conda activate ucla-dev

DEV_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# General
alias d='docker'
alias dc='docker-compose'
alias c="$DEV_PATH/cli.py"

alias adc="docker-compose -f $DEV_PATH/docker-compose.yml -H unix://$DEV_PATH/aws-ec2/docker.sock -p ucla"
alias ad="docker -H unix://$DEV_PATH/aws-ec2/docker.sock"
