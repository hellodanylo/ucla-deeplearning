#!/usr/bin/env zsh
set -eux

conda_path=${0:a:h}

conda env create -n collegium -f $conda_path/conda_collegium.yml
# /app/conda/envs/collegium/bin/python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
conda run -n collegium npm -g install aws-cdk@2.161.0

/app/conda/envs/collegium/bin/ipython kernel install --user --name=collegium

cat - >/app/conda/envs/collegium/lib/python3.10/site-packages/app.pth <<EOF
/home/sagemaker-user
/home/user
/app
EOF


