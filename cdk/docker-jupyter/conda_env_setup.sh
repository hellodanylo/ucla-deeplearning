#!/usr/bin/env zsh

export CONDA_OVERRIDE_CUDA="11.2"
conda env create -n collegium -f ./conda_collegium.yml
/app/miniconda/envs/collegium/bin/ipython kernel install --user --name=collegium
conda run -n collegium npm -g install aws-cdk@2.94.0

cat - >/app/miniconda/envs/collegium/lib/python3.10/site-packages/app.pth <<EOF
/home/sagemaker-user
/home/user
/app
EOF


