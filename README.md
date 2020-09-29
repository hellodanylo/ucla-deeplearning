# Advanced Workshop on Machine Learning

This is the official repository with course material for UCLA Advanced Workshop on Machine Learning (MGMTMSA-434).
The repository will be updated as the course progresses.

The course consists of 5 module:
1. Deep Neural Networks
2. Convolutional Neural Networks
3. Recurrent Neural Networks
4. Generative Adversarial Networks
5. Ensemble Methods

Copyright: Danylo Vashchilenko, 2019.

### Table of Contents
1. [Setup](#setup)
    * [Windows](#windows)
    * [Mac OS](#mac-os)
    * [Dev Tools](#dev-tools)
2. [Jupyter on Local Computer](#jupyter-on-local-computer)
3. [Jupyter on AWS EC2 Instance](#jupyter-on-aws-ec2-instance)

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

## Mac OS
Run the following commands in the terminal:
```
# Install Homebrew: 
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"

# Install Git:
brew install git

# Clone the repository:
git clone --depth 1 https://github.com/hellodanylo/ucla-deeplearning.git

# Install the Miniconda package manager: 
cd ucla-deeplearning
bash ./dev/host_macos.sh
```

Download and install Docker for Mac:
https://hub.docker.com/editions/community/docker-ce-desktop-mac/

In the Docker settings ensure that you have:
* at least 8 GB of memory, preferably around 2/3 of available memory
* all CPUs available on your system

## Dev Tools
Follow this section after you have finished either Windows or Mac OS setup.
Run the following commands in the terminal:
```
# Create ucla-dev environment
conda config --add channels conda-forge
conda env create -n ucla-dev -f dev/conda_init.yml

# Activate the environment:
conda activate ucla-dev

# See the help for available commands:
./dev/cli.py --help
```

# Jupyter on Local Computer

To create and start the Jupyter container:

```
./dev/cli.py jupyter-up
```
You will see a URL and a token in the output. Enter it in the browser.
    
To start the previously stopped Jupyter container:

```
./dev/cli.py jupyter-start
```

To stop the previously started Jupyter container:

```
./dev/cli.py jupyter-stop
```

To stop and remove the Jupyter container:

```
./dev/cli.py jupyter-down
```

# Jupyter on AWS EC2 Instance

First, create a new AWS account and apply credits from AWS Educate.
Run the following commands in the terminal with `ucla-dev` environment activated.
 
To enable access to your AWS account:
```
./dev/cli.py aws-up
```
You can find your AWS credentials at 
[My Credentials](https://console.aws.amazon.com/iam/home?region=us-west-2#/security_credentials)
page.

To create the EC2 instance:
```
./dev/cli.py ec2-up
```

To create a tunnel with the running EC2 instance (do not exit until you are done):
```
./dev/cli.py ec2-tunnel
```
While in the EC2 instance's terminal, you can run `htop` to see CPU cores and CPU RAM utilization.

To create and start the Jupyter container on the EC2 instance:
```
./dev/cli.py jupyter-up --remote
```
You will see a URL and a token in the output. Enter it in the browser.

To change the instance size (for example to p2.xlarge):

```
./dev/cli.py ec2-resize p2.xlarge
```
See the AWS slides for information on available instance sizes.

To install Nvidia drivers, when using GPU instance type (p2 or p3):
```
./dev/cli.py ec2-nvidia
```
While in the EC2 instance's terminal, you can run `nvtop` to see GPU cores and GPU RAM utilization.

To create the remote Jupyter container with GPU support:
```
./dev/cli.py jupyter-up --remote --gpu
```

To stop the EC2 instance (data preserved and billed for):
```
./dev/cli.py ec2-stop
```

To start the instance after it's been stopped:
```
./dev/cli.py ec2-start
```

To remove the EC2 instance (data can't be recovered):
```
./dev/cli.py ec2-down
```

To remove all AWS resources associated with this project:
```
./dev/cli.py aws-down
```