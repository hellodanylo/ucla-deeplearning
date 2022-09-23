#!/usr/bin/env zsh

conda activate ucla-dev

DEV_PATH=${0:a:h}

# General
alias d='docker'
alias dc='docker-compose'
alias c="$DEV_PATH/cli.py"

alias adc="docker-compose -f $DEV_PATH/docker-compose.yml -H unix://$DEV_PATH/aws-ec2/docker.sock -p ucla"
alias ad="docker -H unix://$DEV_PATH/aws-ec2/docker.sock"
