# Advanced Workshop on Machine Learning

https://ccle.ucla.edu/course/view/19F-MGMTMSA434-1?show_all=1

This is the official repository with course material for UCLA Advanced Workshop on Machine Learning (MGMTMSA-434).
The repository will be updated as the course progresses.

The course consists of 5 module:
1. Deep Neural Networks
2. Convolutional Neural Networks
3. Recurrent Neural Networks
4. Generative Adversarial Networks
5. Ensemble Methods

Copyright: Danylo Vashchilenko, 2019.

# Setup

* Install Miniconda package manager (https://docs.conda.io/en/latest/miniconda.html)
* `conda env create -f dev/conda_init.yml`
* `conda activate ucla-dev`
* `aws configure --profile ucla`

# Development CLI
* `./dev/cli.py --help` -- provides help information about every command

# Creating a SageMaker Notebook
* `./dev/cli.py terraform-up`
* `./dev/cli.py sagemaker-up`

# Using a SageMaker Notebook
* `./dev/cli.py sagemaker-start`
* `./dev/cli.py sagemaker-stop`

# Local Jupyter
* `./dev/cli.py jupyter-up`
* `./dev/cli.py jupyter-start`
* `./dev/cli.py jupyter-stop`
* `./dev/cli.py jupyter-down`
