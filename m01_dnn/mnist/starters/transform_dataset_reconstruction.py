#!/usr/bin/env python3
import os

from doctrina.task import execute
from collegium.m01_dnn.mnist.pipelines import build_reconstruction_dataset

execute(
    build_reconstruction_dataset(
        os.environ["APP_STORAGE_WORKSPACE"], seed=42,
    )
)
