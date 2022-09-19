# Advanced Workshop on Machine Learning

This is the official repository with course material for UCLA Advanced Workshop on Machine Learning (MGMTMSA-434).
The repository will be updated as the course progresses.

The course consists of 5 module:
1. Deep Neural Networks
2. Convolutional Neural Networks
3. Recurrent Neural Networks
4. Generative Adversarial Networks
5. Ensemble Methods

Copyright: Danylo Vashchilenko, 2019-2022.

### Table of Contents
1. [Setup](#setup)
    * [Windows](#windows)
    * [Mac OS](#mac-os)
    * [Dev Tools](#dev-tools)
2. [Jupyter on Local Computer](#jupyter-on-local-computer)
3. [Jupyter on AWS SageMaker](#jupyter-on-aws-sagemaker)

# Setup

In order to run the notebooks on your computer and in AWS cloud, you need the following components:
* Git tool to clone this repository
* Miniconda package manager (to install `ucla-dev` environment defined in `./dev/conda_init.yml`)
* Docker for Desktop (to run Jupyter container defined in `./dev/image-python/Dockerfile`)

How to proceed?
* If you are using Windows, follow the instructions under [Windows](#windows)
* If you are using Mac OS, follow the instructions under [Mac OS](#mac-os)

It's strongly advised to use the setup instructions above, but if you would like to manage your own Conda environment:
* the environment for notebooks is defined in: `./dev/docker-jupyter/conda_init.yml`
* Conda channels are defined in: `./dev/docker-jupyter/condarc_student.yml`

## Windows
The following is the summary of these detailed instructions: https://docs.microsoft.com/en-us/windows/wsl/install-win10
1. Check Windows version by running `winver` from you Windows menu
1. If needed, upgrade to Windows 10 v2004 by running "Check for Updates" from your Windows menu
1. Run the following in PowerShell as Administrator:
    ```
    dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
    dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
    ```
1. Restart computer
1. Install WSL update https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi
1. Install Ubuntu 20.04 LTS: https://www.microsoft.com/en-us/p/ubuntu-2004-lts/9n6svws3rx71?rtc=1&activetab=pivot:overviewtab
1. Start Ubuntu shell, and enter a new username and password.
1. Install Docker for Windows: https://hub.docker.com/editions/community/docker-ce-desktop-windows/
1. Start Docker from your Windows menu
   * go to settings and make sure Resources -> WSL Integration has Ubuntu 20.04 enabled
1. Next, restart the Ubuntu shell.
1. Run the following command in Ubuntu shell to download this git repo to `ucla-deeplearning` folder:
    ```
    git clone --depth 1 https://github.com/hellodanylo/ucla-deeplearning.git
    ```
1. Finally, the following script installs Miniconda package manager:
    ```
    cd ucla-deeplearning
    bash ./dev/host_linux.sh
    ```
1. Next, restart the Ubuntu shell.
1. Optionally, run `htop` to monitor your CPU cores and RAM utilization.

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
# Make sure you are in the ucla-deeplearning folder
cd ucla-deeplearning

# Create ucla-dev environment
conda env create -n ucla-dev -f dev/conda_lock.yml

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

# Jupyter on AWS SageMaker

The course instructor has created an AWS user for each student. 
The credentials have been or will be shared with each student directly.

AWS Console login page: https://danylo-ucla.signin.aws.amazon.com/console

In the AWS Console, you can use the following pages:
* list of budgets: https://console.aws.amazon.com/billing/home?#/budgets/overview
* list of SageMaker instances: https://us-west-2.console.aws.amazon.com/sagemaker/home?region=us-west-2#/notebook-instances

## Important: AWS Budgets
Each student is allocated a limited budget per day and per course. 
The budgets page allows to see the current spending per day and per course.

Each day, an automated email will be sent if the spending per day exceeds one of the thresholds.
Throughout the course, an automated email will be sent if the total spending exceeds one of the thresholds.

Each student is responsible for monitoring and planning their AWS budget spending. Exceeding the per-course budget
is considered an error and may impact the assignment grades.
See the budgets page for the current budget information: https://console.aws.amazon.com/billing/home?#/budgets/overview
The per-day and the per-course budgets information is updated every 8-12 hours. 
The per-day budget is computed using 24-hour period in the UTC timezone.

To prevent accidental overspending, the SageMaker instance may automatically stop
when the per-day or per-course spending exceeds the maximum level. 
This mechanism is the final error-prevention measure and should not be relied upon.

## How to open Jupyter in SageMaker?

1. Navigate to the SageMaker notebooks page: https://us-west-2.console.aws.amazon.com/sagemaker/home?region=us-west-2#/notebook-instances
2. Type your username into the search bar to find your instance
3. Open the instance page
4. If the instance is stopped, click `Start`
5. Wait for the instance to start
6. Click `Open JupyterLab`

After opening a particular notebook, select the `ucla_deeplearning` kernel.
Other kernels contain potentially incompatible versions of Tensorflow and other Python packages.

After you are done with Jupyter:
1. Navigate to the SageMaker instances page: https://us-west-2.console.aws.amazon.com/sagemaker/home?region=us-west-2#/notebook-instances
2. Type your username into the search bar to find your instance
3. Open the instance page
4. Click `Stop`

## How to use GPU with Jupyter in SageMaker?

1. Navigate to the SageMaker instances page: https://us-west-2.console.aws.amazon.com/sagemaker/home?region=us-west-2#/notebook-instances
2. Type your username into the search bar to find your instance
3. Open the instance page
4. If the instance is not stopped, click `Stop`
5. Wait for the instance to stop
6. Click `Edit`
7. Change notebook instance type from `ml.t3.xlarge` to `ml.p2.xlarge`
8. Make sure Lifecycle Configuration is set to `ucla-deeplearning-notebook`
9. Click `Update notebook instance`
10. Wait for the instance to update
11. Follow the instance start steps

The GPU instance is 5x-10x more expensive than the non-GPU instance.
Use the GPU instance only when actually needed to train one of the bigger networks.
To revert to the non-GPU instance, follow the steps above but set the instance type to `ml.t3.xlarge`.
