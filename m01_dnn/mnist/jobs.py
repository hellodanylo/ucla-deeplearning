import os
import shutil
from typing import Dict, TypedDict

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split
from tensorflow.keras.callbacks import EarlyStopping, Callback
from tensorflow.keras.datasets import mnist
from tensorflow.keras.layers import Dense
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.initializers import GlorotUniform
import mlflow

from doctrina.dataset import (
    Dataset,
    SegmentDataset,
    DenoisingSegment,
    ReconstructionSegment,
)
from doctrina.keras import save_keras_model
from doctrina.learning_curve import LearningCurve
from doctrina.task import mlflow_run, encode
from collegium.m01_dnn.mnist.report import plot_image_examples


class TransformSplit(TypedDict):
    workdir: str
    segments: Dict[str, float]
    seed: int


def transform_split(task: TransformSplit):
    workdir = task["workdir"]

    (train_X, train_y), (test_X, test_y) = mnist.load_data()

    # Rescale to [0, 1]
    labeled_X = np.concatenate([train_X, test_X]) / 255
    labeled_y = np.concatenate([train_y, test_y])

    # Flattens the spatial dimensions
    labeled_X = labeled_X.reshape([labeled_X.shape[0], -1])

    segment_names = list(sorted(task["segments"].keys()))
    segment_ratios = [task["segments"][name] for name in segment_names]

    n = labeled_y.shape[0]
    segment_count = [round(n * p) for p in segment_ratios]

    remaining_X = labeled_X
    remaining_y = labeled_y

    dataset = Dataset()

    for name, count in zip(segment_names, segment_count):

        if count == remaining_X.shape[0]:
            split_X = remaining_X
            split_y = remaining_y
        else:
            remaining_X, split_X, remaining_y, split_y = train_test_split(
                remaining_X,
                remaining_y,
                test_size=count,
                stratify=remaining_y,
                random_state=task["seed"],
                shuffle=True,
            )

        dataset.__dict__[f"{name}_x"] = pd.DataFrame(
            split_X, columns=map(str, range(split_X.shape[1])), dtype=np.float32
        )

        dataset.__dict__[f"{name}_y"] = pd.DataFrame(split_y, columns=["digit"])

    dataset.to_pq_workdir(workdir)


def add_noise(image: np.ndarray, mean: float, std: float):
    np.random.seed(42)
    noise = np.random.normal(mean, std, image.shape)
    return np.clip(image + noise, 0, 1)


def transform_noisy(task: dict):
    workdir = task["workdir"]

    dataset_workdir = task["upstream"]["transform_split"]["workdir"]

    segment_names = list(sorted(task["upstream"]["transform_split"]["segments"].keys()))

    segment_original = [
        pd.read_parquet(f"{dataset_workdir}/{segment_name}_x.parquet")
        for segment_name in segment_names
    ]

    np.random.seed(task["seed"])

    segment_noisy = [
        pd.DataFrame(
            add_noise(X, task["noise_mean"], task["noise_std"]),
            columns=map(str, range(X.shape[1])),
        )
        for X in segment_original
    ]

    for name, noisy in zip(segment_names, segment_noisy):
        noisy.to_parquet(f"{workdir}/{name}_x.parquet")


def transform_repack(task: dict):
    workdir = task["workdir"]
    split_workdir = task["upstream"]["transform_split"]["workdir"]
    noisy_workdir = task["upstream"]["transform_noisy"]["workdir"]

    segment_names = list(sorted(task["upstream"]["transform_split"]["segments"]))

    for segment_name in segment_names:
        shutil.copyfile(
            f"{noisy_workdir}/{segment_name}_x.parquet",
            f"{workdir}/{segment_name}_noisy_x.parquet",
        )

        if segment_name != "score":
            shutil.copyfile(
                f"{split_workdir}/{segment_name}_x.parquet",
                f"{workdir}/{segment_name}_clean_x.parquet",
            )
            shutil.copyfile(
                f"{split_workdir}/{segment_name}_y.parquet",
                f"{workdir}/{segment_name}_y.parquet",
            )


@mlflow_run
def train_autoencoder(task: dict):
    tf_gpu_init()

    workdir = task["workdir"]

    if task['training_mode'] == 'denoising':
        segment_cls = DenoisingSegment
    elif task['training_mode'] == 'reconstruction':
        segment_cls = ReconstructionSegment

    dataset_task_workdir = task["upstream"][task["dataset_upstream_name"]]["workdir"]
    dataset = SegmentDataset()
    dataset["train"] = segment_cls.from_pq_workdir(
        dataset_task_workdir, "train"
    ).to_regression_segment()
    dataset["validate"] = segment_cls.from_pq_workdir(
        dataset_task_workdir, "validate"
    ).to_regression_segment()

    hyperparams = task["hyperparams"]
    encoder_nodes = hyperparams["encoder_nodes"]
    activation = hyperparams["activation"]
    learning_rate = 10 ** hyperparams["learning_rate_exponent"]

    seed = task["seed"]
    np.random.seed(seed)
    tf.random.set_seed(seed)

    layers = []

    # Encoder layers
    for n in encoder_nodes:
        layers += [
            Dense(
                units=n,
                activation=activation,
                kernel_initializer=GlorotUniform(seed=seed),
            )
        ]

    # Reverse order in the decoder
    # Except for the encoder's innermost layer
    for n in encoder_nodes[-2::-1]:
        layers += [
            Dense(
                units=n,
                activation=activation,
                kernel_initializer=GlorotUniform(seed=seed),
            )
        ]

    layers += [
        Dense(
            units=dataset["train"]["x"].shape[1],
            activation="sigmoid",
            kernel_initializer=GlorotUniform(seed=seed),
        )
    ]

    autoencoder = Sequential(layers)
    autoencoder.compile(
        optimizer=Adam(learning_rate=learning_rate),
        loss=hyperparams["loss_function"]
    )

    callbacks = []

    if "early_stopping" in task:
        callbacks.append(
            EarlyStopping(
                monitor="loss",
                baseline=task["early_stopping"]["baseline"],
                min_delta=task["early_stopping"]["delta"],
                patience=task["early_stopping"]["patience"],
            )
        )

    callbacks.append(MlflowCallback())

    history = autoencoder.fit(
        x=dataset["train"]['x'].values,
        y=dataset["train"]['y'].values,
        batch_size=hyperparams["batch_size"],
        epochs=task["epochs"],
        validation_data=[
            dataset["validate"]['x'].values,
            dataset["validate"]['y'].values,
        ],
        callbacks=callbacks,
        verbose=task.get("verbose", "auto"),
    )

    dataset['train']['y_hat'] = pd.DataFrame(autoencoder.predict(dataset["train"]["x"]))

    if task['training_mode'] == 'denoising':
        fig = plot_image_examples(
            dataset["train"],
            ['y', 'x', 'y_hat'],
            n_examples=3,
            seed=100
        )
        fig.savefig(f"{workdir}/example_denoising.svg")
    else:
        fig = plot_image_examples(
            dataset['train'],
            ['x', 'y_hat'],
            n_examples=3,
            seed=100
        )
        fig.savefig(f"{workdir}/example_reconstruction.svg")

    curve = LearningCurve.from_history_with_segments(dataset, autoencoder, history)
    curve.to_workdir(workdir)
    curve.save_png(workdir)
    curve.to_mlflow()

    save_keras_model(workdir, autoencoder)


class MlflowCallback(Callback):
    def on_epoch_end(self, epoch: int, logs: Dict[str, float]):
        mlflow.log_metrics(metrics=logs, step=epoch)


def tf_gpu_init():
    gpus = tf.config.experimental.list_physical_devices("GPU")
    if gpus:
        try:
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
        except RuntimeError as e:
            print(e)


def build_autoencoder_task(is_test: bool, training_mode: str):
    workspace = os.environ['APP_STORAGE_WORKSPACE']
    experiment = f"train_{training_mode}_{'tiny' if is_test else 'full'}"

    return {
        "workspace": workspace,
        "function": encode(train_autoencoder),
        "experiment": experiment,
        "training_mode": training_mode,
        # Inferred from search_is_01
        "seed": 908616996,
        "hyperparams": {
            "encoder_nodes": [200, 100] if not is_test else [10],
            "activation": "elu",
            "batch_size": 128 if not is_test else 5000,
            # Inferred from search_lr_01
            "learning_rate_exponent": -2.5,
            'loss_function': 'mean_squared_error',
        },
        "epochs": 100 if not is_test else 3,
        "early_stopping": {
            "baseline": 0.1,
            "delta": 0.0001,
            "patience": 5,
        },
        "dataset_upstream_name": "transform_split" if training_mode == 'reconstruction' else 'transform_repack',
    }
