#!/usr/bin/env bash

set -e

PROJECT_PATH=/home/ec2-user/SageMaker/setup
sudo -u ec2-user -i mkdir -p "$PROJECT_PATH"

sudo -u ec2-user tee "$PROJECT_PATH/conda_lock.yml" <<'EOF'
${conda_lock_yml}
EOF

sudo -u ec2-user tee >"$PROJECT_PATH/setup.sh" <<'EOF'
#!/usr/bin/env bash

name="${sagemaker_notebook_name}"



conda activate JupyterSystemEnv
jupyter labextension install --no-build jupyterlab_vim
jupyter labextension install --no-build @jupyter-widgets/jupyterlab-manager
jupyter lab build

PROJECT_PATH=/home/ec2-user/SageMaker/setup
wget https://repo.anaconda.com/miniconda/Miniconda3-py37_4.8.3-Linux-x86_64.sh -O "$PROJECT_PATH/miniconda.sh"
bash "$PROJECT_PATH/miniconda.sh" -b -u -p "$PROJECT_PATH/miniconda"
rm -rf "$PROJECT_PATH/miniconda.sh"

source $PROJECT_PATH/miniconda/bin/activate
conda env create -n ucla_deeplearning -q -f "$PROJECT_PATH/conda_lock.yml"

touch $PROJECT_PATH/done.txt
aws dynamodb update-item \
  --table-name ucla-deep-learning-notebooks \
  --key {\"name\":{\"S\":\"$name\"}} \
  --attribute-updates {\"state\":{\"Value\":{\"S\":\"installed\"}}}


EOF
chmod +x "$PROJECT_PATH/setup.sh"

nohup sudo -u ec2-user -i bash -l "$PROJECT_PATH/setup.sh" >"$PROJECT_PATH/setup.log" &