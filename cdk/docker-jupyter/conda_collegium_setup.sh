#!/usr/bin/env zsh
set -eux

conda_path=${0:a:h}

conda env create -p /opt/conda/envs/cdk -f $conda_path/conda_collegium.yml
conda run -n cdk npm -g install aws-cdk@2.1031.1

cat - >/opt/conda/envs/cdk/lib/python3.12/site-packages/app.pth <<EOF
/app
EOF
