#!/usr/bin/env bash

set -e

sudo -u ec2-user -i <<'EOF'
  unset SUDO_UID
  PROJECT_PATH=/home/ec2-user/SageMaker/setup

  source "$PROJECT_PATH/miniconda/bin/activate"
  conda init
  conda activate ucla_deeplearning
  python -m ipykernel install --user --name ucla_deeplearning

  sudo yum install -y htop
EOF