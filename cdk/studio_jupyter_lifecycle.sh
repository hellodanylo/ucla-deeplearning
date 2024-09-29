#!/usr/bin/env bash

# This script assumes the SageMaker Studio Jupyter environment.
# It appears to have a Conda environment with Python that can be used below.
# Based on https://github.com/aws-samples/amazon-sagemaker-codeserver/blob/cc153da6be44c92d2b5cf0115ac61c746b57c25e/install-scripts/studio/install-codeserver.sh

git clone --depth 1 https://github.com/hellodanylo/ucla-deeplearning collegium

sudo yum install -y vim wget zsh

mkdir -p $HOME/.collegium
cd $HOME/.collegium
wget -O sagemaker-jproxy-launcher-ext-0.1.3.tar.gz https://github.com/aws-samples/amazon-sagemaker-codeserver/releases/download/v0.1.5/sagemaker-jproxy-launcher-ext-0.1.3.tar.gz
conda run -n studio pip install sagemaker-jproxy-launcher-ext-0.1.3.tar.gz
conda run -n studio jupyter labextension disable jupyterlab-server-proxy

sudo yum install unzip
aws s3 cp s3://danylo-ucla/mlflow.zip ./
unzip mlflow.zip -d /opt/conda/envs
rm mlflow.zip
# Logo for the launch icon is required and must be SVG
wget -O /opt/conda/envs/mlflow/icon.svg https://raw.githubusercontent.com/hellodanylo/ucla-deeplearning/refs/heads/main/cdk/docker-jupyter/mlflow.svg

# This Jupyter proxy and MLFlow will run on the JupyterServer instance,
# where the Collegium image is not used. So the path to EFS is via /home/sagemaker-user.
mkdir -p $HOME/.jupyter
cat - >$HOME/.jupyter/jupyter_notebook_config.py <<EOF
c.ServerProxy.servers = {
        "mlflow": {
            "command": ["/opt/conda/envs/mlflow/bin/python", "-m", "mlflow", "server", "--port", "{port}", "--backend-store-uri", "file:///home/sagemaker-user/mlflow"],
            'launcher_entry': {
                'enabled': True,
                'title': 'mlflow',
                'icon_path': '/opt/conda/envs/mlflow/icon.svg'
            },
            'environment': {
                "PATH": '/opt/conda/envs/mlflow/bin',
            },
            "timeout": 60,
        }
}
EOF

restart-jupyter-server

echo "Revision {revision}" >~/.jupyter/studio_jupyter_revision
