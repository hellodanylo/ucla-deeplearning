#!/usr/bin/env bash

# This script assumes the SageMaker Studio Jupyter environment.
# It appears to have a Conda environment with Python that can be used below.
# Based on https://github.com/aws-samples/amazon-sagemaker-codeserver/blob/cc153da6be44c92d2b5cf0115ac61c746b57c25e/install-scripts/studio/install-codeserver.sh

pip install git-remote-codecommit
git clone --depth 1 codecommit::us-west-2://collegium

sudo yum install -y vim wget zsh

mkdir -p $HOME/.collegium
cd $HOME/.collegium
wget -O sagemaker-jproxy-launcher-ext-0.1.3.tar.gz https://github.com/aws-samples/amazon-sagemaker-codeserver/releases/download/v0.1.5/sagemaker-jproxy-launcher-ext-0.1.3.tar.gz
conda run -n studio pip install sagemaker-jproxy-launcher-ext-0.1.3.tar.gz
conda run -n studio jupyter labextension disable jupyterlab-server-proxy

conda create -n mlflow
conda install -n mlflow python==3.11.5
conda run -n mlflow pip install mlflow==2.6.0

# Logo for the launch icon is required and must be SVG
wget -O /opt/conda/envs/mlflow/icon.svg https://raw.githubusercontent.com/mlflow/mlflow/master/assets/icon.svg

mkdir -p $HOME/.jupyter
cat - >$HOME/.jupyter/jupyter_notebook_config.py <<EOF
c.ServerProxy.servers = {
        "mlflow": {
            "command": ["/opt/conda/envs/mlflow/bin/python", "-m", "mlflow", "server", "--port", "{port}", "--backend-store-uri", "file:///app/mlflow"],
            'launcher_entry': {
                'enabled': True,
                'title': 'mlflow',
                'icon_path': '/app/miniconda/envs/jupyter/mlflow.svg'
            },
            'environment': {
                "PATH": '/opt/conda/envs/mlflow/bin',
            },
            "timeout": 60,
        }
}
EOF

restart-jupyter-server

echo "Revision {revision}" >version
