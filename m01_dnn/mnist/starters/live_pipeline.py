#!/usr/bin/env python

from collections import OrderedDict

from doctrina.pipeline import execute_pipeline
from doctrina.task import execute, encode
from collegium.m01_dnn.mnist.jobs import transform_split, train_autoencoder

execute({
    'workspace': 'mnist',
    'function' : encode(execute_pipeline),

    'stages'   : OrderedDict(

        transform_dataset={
            'workspace': 'mnist',
            'function' : encode(transform_split),
            'seed'     : 42,
            'segments': {
                'train': 0.8,
                'validate': 0.1,
                'test': 0.1,
            }
        },

        train_autoencoder={
            'workspace'              : 'mnist',
            'function'               : encode(train_autoencoder),
            'experiment': 'live_pipeline',
            'training_mode': 'reconstruction',
            'dataset_upstream_name': 'transform_dataset',

            # Inferred from initialization_seed_v10
            'seed'                   : 1664456243,

            'hyperparams'            : {
                'encoder_nodes': [100],
                'activation'   : 'elu',
                'batch_size'   : 32,
                'learning_rate': 0.001,
            },

            'early_stopping_baseline': 0.2,
            'early_stopping_delta'   : 0.01,
            'early_stopping_patience': 5,

            'epochs'                 : 100,
        }

    )
})
