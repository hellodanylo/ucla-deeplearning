#!/usr/bin/env python3
import os
import random

from doctrina.pipeline import execute_pipeline
from doctrina.task import encode, get_task_workdir, execute
from doctrina.util import send_slack
from collegium.m01_dnn.mnist.jobs import train_autoencoder
import mlflow

workspace = os.environ["APP_STORAGE_WORKSPACE"]
experiment = "search_is_01"
total_jobs = 100
concurrent_jobs = 8

# To prevent a race condition among the parallel stages
if mlflow.get_experiment_by_name(experiment) is None:
    mlflow.create_experiment(experiment)

execute(
    {
        "workspace": workspace,
        "function": encode(execute_pipeline),
        "resume": get_task_workdir(
            workspace,
            execute_pipeline.__name__,
            "20230903-212050_8430596ef0a8d9c71e7338368691cfa9",
        ),
        "parallel_processes": concurrent_jobs,
        "stages": {
            "train_autoencoders": [
                {
                    "function": encode(train_autoencoder),
                    "training_mode": "reconstruction",
                    "seed": random.randint(0, (2 ** 32) - 1),
                    "hyperparams": {
                        # Inferred from search_ew_01
                        "encoder_nodes": [100],
                        "activation": "elu",
                        "batch_size": 128,
                        # Inferred from search_lr_01
                        "learning_rate_exponent": -2.5,
                        'loss_function': 'mean_squared_error'
                    },
                    "verbose": 0,
                    "epochs": 20,
                    "dataset_upstream_name": "transform_split",
                    "experiment": experiment,
                    "workspace": workspace,
                }
                for _ in range(total_jobs)
            ]
        },
    }
)
