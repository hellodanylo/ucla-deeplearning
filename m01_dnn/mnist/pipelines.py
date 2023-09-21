from collections import OrderedDict

from doctrina.pipeline import execute_pipeline
from doctrina.task import encode
from collegium.m01_dnn.mnist.jobs import transform_split, transform_noisy, transform_repack


def build_denoising_dataset(workspace: str, split_seed: int, noise_seed: int):
    return {
        'workspace': workspace,
        'function': encode(execute_pipeline),

        'stages': OrderedDict(
            transform_split={
                'workspace': workspace,
                'function': encode(transform_split),
                'seed': split_seed,
                'segments': {
                    'train': 0.7,
                    'validate': 0.1,
                    'test': 0.1,
                    'score': 0.1
                }
            },

            transform_noisy={
                'workspace': workspace,
                'function': encode(transform_noisy),
                'seed': noise_seed,
                'noise_mean': 0,
                'noise_std': 0.20,
            },

            transform_repack={
                'workspace': workspace,
                'function': encode(transform_repack)
            },
        )
    }


def build_reconstruction_dataset(workspace: str, seed: int):
    return {
        'workspace': workspace,
        'function': encode(execute_pipeline),
        'stages': {
            'transform_split': {
                'workspace': workspace,
                'function' : encode(transform_split),
                'seed'     : seed,
                'segments': {
                    'train': 0.8,
                    'validate': 0.1,
                    'test': 0.1,
                }
            },
        }
    }
