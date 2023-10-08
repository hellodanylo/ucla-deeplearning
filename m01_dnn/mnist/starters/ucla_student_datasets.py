#!/usr/bin/env python
import os
import random
from collections import OrderedDict
from doctrina.pipeline import execute_pipeline
from doctrina.task import execute, encode

from collegium.m01_dnn.mnist.pipelines import build_denoising_dataset

students = 50

workspace = os.environ["APP_STORAGE_WORKSPACE"]

execute(
    {
        "workspace": workspace,
        "function": encode(execute_pipeline),
        "parallel_processes": 1,
        "stages": OrderedDict(
            dataset=[
                build_denoising_dataset(
                    workspace,
                    split_seed=random.randint(0, (2 ** 32) - 1),
                    noise_seed=random.randint(0, (2 ** 32) - 1),
                )
                for s in range(students)
            ]
        ),
    }
)
