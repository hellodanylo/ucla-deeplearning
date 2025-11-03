#!/usr/bin/env zsh
set -eux

conda_path=${0:a:h}

conda env create -p /opt/conda/envs/collegium -f $conda_path/conda_collegium.yml
conda run -n collegium npm -g install aws-cdk@2.161.0

cat - >/opt/conda/envs/collegium/lib/python3.12/site-packages/app.pth <<EOF
/app
EOF
