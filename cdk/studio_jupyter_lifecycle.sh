#!/usr/bin/env bash

# This script assumes the SageMaker Studio Jupyter environment.
# It appears to have a Conda environment with Python that can be used below.
# Based on https://github.com/aws-samples/amazon-sagemaker-codeserver/blob/cc153da6be44c92d2b5cf0115ac61c746b57c25e/install-scripts/studio/install-codeserver.sh

cd ~
ls collegium || git clone --depth 1 https://github.com/hellodanylo/ucla-deeplearning collegium
