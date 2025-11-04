![Robot teacher in class in front of a blackboard with math equations](./header.png)
(Image by a Stable Diffusion model using prompt "robot teacher in class, math equations on blackboard, cartoon style, steampunk")

# Advanced Workshop on Machine Learning

This is the official repository with course material for UCLA Advanced Workshop on Machine Learning (MGMTMSA-434).
The repository will be updated as the course progresses.

The course consists of 5 module:
1. Deep Neural Networks
2. Convolutional Neural Networks
3. Recurrent Neural Networks
4. Generative Networks
5. Ensemble Methods

Copyright: Danylo Vashchilenko, 2019-2025.

# AWS SageMaker

The course instructor has created an AWS user for each student. 
The credentials have been or will be shared with each student directly.

AWS Console login page: https://danylo-ucla.signin.aws.amazon.com/console

In the AWS Console, you can use the following pages:
* Budgets: https://console.aws.amazon.com/billing/home?#/budgets/overview
* SageMaker Studio: https://us-west-2.console.aws.amazon.com/sagemaker/home?region=us-west-2#/studio

## Important: AWS Budgets
Each student is allocated a limited budge per course. 
The budgets page allows to see the current spending.
Throughout the course, an automated email will be sent if the total spending exceeds one of the thresholds.

Each student is responsible for monitoring and planning their AWS budget spending. Exceeding the per-course budget
is considered an assignment error and may impact the assignment grades.
The budgets information is updated every 12 hours with a 24-hour delay.

## How to open Jupyter via SageMaker Studio?

1. Navigate to the SageMaker Domains page: https://us-west-2.console.aws.amazon.com/sagemaker/home?region=us-west-2#/studio
2. Open the SageMaker domain `ucla-deeplearning`
3. Click on the User profiles tab
4. Type your username into the search bar to find your profile
5. Open the profile page
6. Click Launch -> Studio
7. Click JupyterLab
8. Open the space with your username
9. Select one of approved Instance types (see section below)
10. Select Image `collegium`
11. Select Lifecycle Configuration `collegium`
12. Click Run Space

After ~10 minutes, the space will transition from "Starting" to "Running" state. You will see "Open JupyterLab" button available. In Jupyter, the course materials are available in `collegium` directory of your space.

## What is a SageMaker Space?

A space is an allocation of persistent user-private storage that is used with Jupyter.
It's the workspace where you can save your notebooks, data, models, while you are taking this course.
Every student in the course has one space created for them automatically.
In Jupyter, this persistent storage is available as `/home/sagemaker-user`. All other parts of the file system will reset whenever the space is stopped.
This space is persistent regardless of whether Jupyter application is currently running or not.
You are billed for compute whenever the space is in "Running" state. You are billed for
storage regardless of whether the space is running or not.

## Which instance type should I use?

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
