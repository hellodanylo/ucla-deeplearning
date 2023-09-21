#!/usr/bin/env python3
import os

from doctrina.pipeline import execute_pipeline
from doctrina.task import execute, encode, get_task_workdir
from collegium.m01_dnn.mnist.jobs import build_autoencoder_task

workspace = os.environ['APP_STORAGE_WORKSPACE']

execute(
    {
        "workspace": workspace,
        "function": encode(execute_pipeline),
        "resume": get_task_workdir(
            workspace,
            execute_pipeline.__name__,
            "20230903-212050_8430596ef0a8d9c71e7338368691cfa9",
        ),
        "parallel_processes": 1,
        "stages": {
            "train_autoencoder": build_autoencoder_task(is_test=False, training_mode='reconstruction')
        }
    }
)
