#!/usr/bin/env python3
import os
import random

from doctrina.pipeline import execute_pipeline
from doctrina.task import encode, get_task_workdir, execute
from doctrina.util import send_slack
from mnist.jobs import train_autoencoder

workspace = os.environ["APP_STORAGE_WORKSPACE"]
experiment = "search_is_03"
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
