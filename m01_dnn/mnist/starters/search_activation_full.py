#!/usr/bin/env python3
import random

from joblib import Parallel, delayed

from doctrina.task import get_last_workdir, execute
from doctrina.util import send_slack
from collegium.m01_dnn.mnist.jobs import transform_split, train_autoencoder

search_group = 'activation_v1'
total_jobs = 16
concurrent_jobs = 3

jobs = [delayed(execute)({

    'workspace'      : 'mnist',
    'job'            : train_autoencoder.__name__,

    'dataset_workdir': get_last_workdir('mnist', transform_split.__name__),
    'seed'           : random.randint(0, (2**32)-1),

    'hyperparams'    : {
        'encoder_nodes': [64, 32, 16],
        'activation'   : random.choice(['elu', 'relu']),
        'batch_size'   : 32,

        # Inferred from learning_rate_v4 search group
        'learning_rate': 10 ** -6.1
    },

    'epochs'         : 20,

    'tags'           : {
        'search_group': search_group
    }

}) for i in range(total_jobs)]

Parallel(n_jobs=concurrent_jobs, verbose=10)(jobs)

send_slack(
    f'Search Completed: {search_group} (n = {total_jobs})',
    []
)
