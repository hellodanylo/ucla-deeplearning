#!/usr/bin/env python3
import os

from doctrina.pipeline import execute_pipeline
from doctrina.task import execute, encode, get_task_workdir
from collegium.m01_dnn.assignment.jobs import build_autoencoder_task

workspace = os.environ['APP_STORAGE_WORKSPACE']

execute(
    {
        "workspace": workspace,
        "function": encode(execute_pipeline),
        "resume": get_task_workdir(
            workspace,
            execute_pipeline.__name__,
            "20230902-103819_9e73e81f0b4e56f9a515fa0fd5561310",
        ),
        "parallel_processes": 1,
        "stages": {
            "train_autoencoder": build_autoencoder_task(is_test=True, training_mode='reconstruction')
        }
    }
)
