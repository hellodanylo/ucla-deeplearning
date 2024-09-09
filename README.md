![Robot teacher in class in front of a blackboard with math equations](./header.png)
(Image by a Stable Diffusion model using prompt "robot teacher in class, math equations on blackboard, cartoon style, steampunk")

# Advanced Workshop on Machine Learning

This is the official repository with course material for UCLA Advanced Workshop on Machine Learning (MGMTMSA-434).
The repository will be updated as the course progresses.

The course consists of 5 module:
1. Deep Neural Networks
2. Convolutional Neural Networks
3. Recurrent Neural Networks
4. Generative Adversarial Networks
5. Ensemble Methods

Copyright: Danylo Vashchilenko, 2019-2024.

### Table of Contents
1. [AWS SageMaker](#jupyter-on-aws-sagemaker)

# AWS SageMaker

The course instructor has created an AWS user for each student. 
The credentials have been or will be shared with each student directly.

AWS Console login page: https://danylo-ucla.signin.aws.amazon.com/console

In the AWS Console, you can use the following pages:
* Budgets: https://console.aws.amazon.com/billing/home?#/budgets/overview
* SageMaker Studio: https://us-west-2.console.aws.amazon.com/sagemaker/home?region=us-west-2#/studio

## Important: AWS Budgets
Each student is allocated a limited budget per day and per course. 
The budgets page allows to see the current spending per day and per course.

Each day, an automated email will be sent if the spending per day exceeds one of the thresholds.
Throughout the course, an automated email will be sent if the total spending exceeds one of the thresholds.

Each student is responsible for monitoring and planning their AWS budget spending. Exceeding the per-course budget
is considered an assignment error and may impact the assignment grades.
The per-day and the per-course budgets information is updated every 8-12 hours. 
The per-day budget is computed using a 24-hour period in the UTC timezone.

## How to open Jupyter via SageMaker Studio?

1. Navigate to the SageMaker Domains page: https://us-west-2.console.aws.amazon.com/sagemaker/home?region=us-west-2#/studio
2. Open the SageMaker domain
3. Type your username into the search bar to find your profile
4. Open the profile page
5. Click Launch -> Studio

SageMaker Studio refers to the AWS version of Jupyter.

## Studio Resources

Before starting using notebooks in Studio, it's important to understand the relationship
between different types of resources that SageMaker creates for you.

Terminology used in SageMaker Studio:
* Instance = Virtual Machine = 1 unit of billable compute resource
* App = Kernel Gateway = 1 Docker container running on 1 Instance
* Session = Notebook Kernel = 1 Jupyter notebook running in 1 App
* Image = Docker Image = an environment with pre-installed software packages

Each Instance has 1 or more Apps.
Each App has 1 or more Sessions.
Each Session has exactly 1 notebook.

#### Resource Reuse
When you launch a kernel, SageMaker will attempt to re-use instances and apps that are already running.
The following table summarizes SageMaker's action depending on whether requested resources are already running.

|Same instance type?|Same image, startup script, and kernel?|SageMaker's action on session launch|
|--|--|--|
|Yes|Yes|Re-use instance and app
|Yes||Re-use instance, but start new app
|||Start new instance, start new app

## Checklist
You should make sure that are able to do the following actions before starting any assignment in this course:
* check whether any billable resources are running via Console UI
* check whether any billable resources are running via Jupyter UI
* start a new Session on a new Instance
* start a new Session on an existing Instance
* stop an existing Session
* stop an App via Jupyter UI
* stop an App via Console UI

### Starting a new Session

* Image = `collegium`, make sure to use the latest version
* Kernel = `collegium`
* Instance type = see section on instance types below
* Startup Script = `collegium-kernel`, make sure to use the latest version

The Collegium image's size is ~10GB, so it might take ~5 minutes to download it to a new instance.
Once the image is downloaded to the instance, starting additional apps will take only seconds.
While the image is being downloaded, the Jupyter UI will report "Starting notebook kernel...", and the Console UI will report the Kernel Gateway in Pending status.

**Important**: the session launch will continue even if the Jupyter UI is closed (e.g. you close the browser).
If you would like to stop the use of billable compute resources, you need to explicitly stop all running apps in Jupyter UI or Studio Console.


## Instance Types

This course's assignments have been designed to be solved with the following instance types:

|Instance Type|CPU cores|CPU RAM|GPU VRAM|Cost ratio|
|--|--|--|--|--|
|ml.t3.xlarge|4|16||1x|
|ml.t3.2xlarge|8|32||2x|
|ml.g4dn.4xlarge|16|64|16|7.5x|

In order to maximize the cost efficiecy, it's recommend to prototype with the cheaper non-GPU instance.
When the training code is stable, you can switch to the GPU instance for fast training.
For example, the training code can be tested with a batch size of 1 without a GPU. 
The GPU instance is 7.5x more expensive than the base CPU instance.
You should use the GPU instance only when actually needed to train one of the bigger networks.

