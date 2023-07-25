#!/usr/bin/env python3
import os
import random

from doctrina.pipeline import execute_pipeline
from doctrina.task import encode, get_task_workdir, execute
from doctrina.util import send_slack
from collegium.m01_dnn.assignment.jobs import train_autoencoder

workspace = os.environ["APP_STORAGE_WORKSPACE"]
experiment = "search_lr_03"
total_jobs = 100
concurrent_jobs = 1

execute(
    {
        "workspace": workspace,
        "function": encode(execute_pipeline),
        "resume": get_task_workdir(
            workspace,
            execute_pipeline.__name__,
            "20200906-222117_d1d6ccdc65e33085493262d3553282c0",
        ),
        "parallel_processes": concurrent_jobs,
        "stages": {
            "train_autoencoders": [
                {
                    "function": encode(train_autoencoder),
                    "training_mode": "reconstruction",
                    # Inferred from initialization_seed_v4 search group
                    "seed": 3488065078,
                    "hyperparams": {
                        "encoder_nodes": [10],
                        "activation": "elu",
                        "batch_size": 128,
                        "learning_rate_exponent": random.uniform(-6, 1),
                        'loss_function': 'mean_squared_error'
                    },
                    "epochs": 20,
                    "dataset_upstream_name": "transform_split",
                    "experiment": experiment,
                    "workspace": workspace,
                }
                for i in range(total_jobs)
            ]
        },
    }
)

send_slack(f"Search Completed: {experiment} (n = {total_jobs})", [])
