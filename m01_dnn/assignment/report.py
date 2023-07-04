from typing import Dict

import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

from doctrina.learning_curve import LearningCurve


def plot_learning_curves(
    learning_curves: Dict[str, LearningCurve],
    loss_function: str,
    differentiator_name: str,
    differentiator_values: Dict[str, object],
    loss_min_max: tuple = None,
    title: str = "Learning Curves",
):
    learning_metas = []
    for workdir, curve in learning_curves.items():
        curve = curve.learning_scores.reset_index()
        curve.index = curve.index + 1
        curve["workdir"] = workdir
        curve[differentiator_name] = differentiator_values[workdir]
        learning_metas.append(curve)

    fig = plt.figure(figsize=[8, 4], dpi=200)
    plt.title(title)
    fig.patch.set_facecolor("lightgrey")

    learning_metas = pd.concat(learning_metas)

    sns.lineplot(
        x="epoch",
        y=(loss_function, "train"),
        hue=differentiator_name,
        units="workdir",
        palette=plt.get_cmap("coolwarm"),
        legend="brief",
        estimator=None,
        data=learning_metas,
    )

    if loss_min_max is not None:
        plt.ylim(loss_min_max)

    return fig


def plot_image(pixels: np.array):
    side = 28
    plt.imshow(pixels.reshape(side, side), cmap="binary")
    plt.yticks([])
    plt.xticks([])


def plot_image_examples(segment, frame_names, n_examples, seed=None):
    n_cols = len(frame_names)
    n_rows = n_examples
    n_sample = segment[frame_names[0]].shape[0]

    if seed is not None:
        np.random.seed(seed)

    idx = np.random.randint(0, n_sample, n_rows)

    fig = plt.figure(figsize=[3 * n_cols, 3 * n_rows], dpi=200)
    fig.patch.set_facecolor('lightgrey')

    for r in range(n_rows):
        for c, frame_name in enumerate(frame_names):
            plt.subplot(n_rows, n_cols, r * n_cols + c + 1)
            plt.title(frame_name)
            plot_image(segment[frame_name].iloc[idx[r]].values)

    plt.tight_layout()
    return fig
