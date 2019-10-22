#!/bin/bash

sudo -u ec2-user -i <<'EOF'

source activate tensorflow_p36
conda install -y tensorflow-hub seaborn ffmpeg
source deactivate

sudo yum install -y htop

EOF
