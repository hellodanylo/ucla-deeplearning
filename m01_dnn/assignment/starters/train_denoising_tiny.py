#!/usr/bin/env python3
import os

from doctrina.pipeline import execute_pipeline
from doctrina.task import execute, encode, get_task_workdir
from mnist.jobs import build_autoencoder_task

workspace = os.environ['APP_STORAGE_WORKSPACE']

execute(
    {
        "workspace": workspace,
        "function": encode(execute_pipeline),
        "resume": get_task_workdir(
            workspace,
            execute_pipeline.__name__,
            "20200906-222117_d1d6ccdc65e33085493262d3553282c0",
        ),
        "parallel_processes": 1,
        "stages": {
            "train_autoencoder": build_autoencoder_task(is_test=True, training_mode='denoising')
        }
    }
)
