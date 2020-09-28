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

In order to run the notebooks on your computer and in AWS cloud, you need the following components:
* Git tool to clone this repository
* Miniconda package manager (to install `ucla-dev` environment defined in `./dev/conda_init.yml`)
* Docker for Desktop (to run Jupyter container defined `./dev/image-python/Dockerfile`)

How to proceed?
* If you are using Windows, follow the instructions under [Windows](#windows)
* If you are using Mac OS, follow the instructions under [Mac OS](#macos)

It's strongly advised to use the setup instructions above, but if you would like to manage your own Conda environment:
* the environment for notebooks defined in: `./dev/docker-jupyter/conda_init.yml`
* Conda channels defined in: `./dev/docker-jupyter/condarc_student.yml`

## Windows
The following is the summary of these detailed instructions: https://docs.microsoft.com/en-us/windows/wsl/install-win10
1. Upgrade to Windows 10 v2004 
2. Run the following in PowerShell as Administrator:
    ```
    dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
    dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
    ```
3. Restart computer
4. Install WSL update https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi
5. Install Docker for Windows: https://hub.docker.com/editions/community/docker-ce-desktop-windows/
6. Install Ubuntu 20.04 LTS: https://www.microsoft.com/en-us/p/ubuntu-2004-lts/9n6svws3rx71?rtc=1&activetab=pivot:overviewtab
7. Start Ubuntu shell, and enter a new username and password.
8. Run the following command in Ubuntu shell to download this git repo to `$HOME/git/ucla-deeplearning`
    ```
    mkdir git 
    git clone https://github.com/hellodanylo/ucla-deeplearning.git ~/git/ucla-deeplearning
    ```
9. Next, restart the Ubuntu shell.
10. Finally, the following script installs Miniconda package manager:
    ```
     cd ~/git/ucla-deeplearning
    ./dev/host_linux.sh
    ```

## MacOS
Run the following commands in the terminal:
```
# Install Homebrew: 
sudo /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"

# Install Git:
brew install git

# Clone the repository:
git clone https://github.com/hellodanylo/ucla-deeplearning.git

# Install the Miniconda package manager: 
cd ucla-deeplearning
./dev/host_macos.sh
```

[](#setup-development-cli)
# Setup: Development CLI
Run the following commands in the terminal:
```
# Create ucla-dev environment
conda env create -f dev/conda_init.yml

# Activate the environment:
conda activate ucla-dev

# See the help for available commands:
./dev/cli.py --help
```

# Local Jupyter
* `./dev/cli.py jupyter-up`
* `./dev/cli.py jupyter-start`
* `./dev/cli.py jupyter-stop`
* `./dev/cli.py jupyter-down`

# AWS SageMaker Notebook

1. Setup an AWS Account:
    ```
    ./dev/cli.py aws-init
    ```
2. Create a SageMaker Notebook:
    ```
    ./dev/cli.py s3-up
    ./dev/cli.py sagemaker-up
    ```
3. Start a SageMaker Notebook
    ```
    ./dev/cli.py sagemaker-start
    ```
4. You will see a URL in the output. Enter it in the browser.
5. To stop using the SageMaker compute resources (data can be recovered):
    ```
    ./dev/cli.py sagemaker-stop
    ```
6. To stop using the SageMaker storage resources (data can't be recovered):
    ```
    ./dev/cli.py sagemaker-down
    ./dev/cli.py s3-down
    ```
