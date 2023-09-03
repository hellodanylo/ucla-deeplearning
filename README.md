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

Copyright: Danylo Vashchilenko, 2019-2022.

### Table of Contents
1. [Jupyter on AWS SageMaker](#jupyter-on-aws-sagemaker)

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
is considered a human error and may impact the assignment grades.
See the budgets page for the current budget information: https://console.aws.amazon.com/billing/home?#/budgets/overview
The per-day and the per-course budgets information is updated every 8-12 hours. 
The per-day budget is computed using 24-hour period in the UTC timezone.

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

1. Navigate to the SageMaker Domains page: https://us-west-2.console.aws.amazon.com/sagemaker/home?region=us-west-2#/studio
2. Open the SageMaker domain
3. Type your username into the search bar to find your profile
4. Open the profile page
5. Click Launch -> Studio

The GPU instance is 5x-10x more expensive than the non-GPU instance.
Use the GPU instance only when actually needed to train one of the bigger networks.
To revert to the non-GPU instance, follow the steps above but set the instance type to `ml.t3.4xlarge`.

