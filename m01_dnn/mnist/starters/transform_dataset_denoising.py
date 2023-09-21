#!/usr/bin/env python3
import os

from doctrina.task import execute
from collegium.m01_dnn.mnist.pipelines import build_denoising_dataset

execute(
    build_denoising_dataset(
        os.environ["APP_STORAGE_WORKSPACE"], split_seed=42, noise_seed=42,
    )
)
