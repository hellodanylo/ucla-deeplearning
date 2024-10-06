from typing import Optional
import zipfile
import PIL.Image
from keras.applications.mobilenet import preprocess_input

import numpy as np
import tensorflow as tf


def load_images(segment: str, limit: Optional[int] = None, preprocess: bool = True):
    with zipfile.ZipFile('pnp_dataset.zip') as z:

        targets = sorted(p for p in z.namelist() if p.startswith(f'pnp_dataset/{segment}') and 'npy' not in p)
        if limit is not None:
            targets = targets[:limit]

        for _, target in enumerate(targets):
            with z.open(target) as f:
                image_pixels = np.array(PIL.Image.open(f), dtype=np.float32)
                if preprocess:
                    image_pixels = preprocess_input(image_pixels)
                yield image_pixels.astype(np.float16)

def load_labels(segment: str, limit: Optional[int] = None):
    with zipfile.ZipFile('pnp_dataset.zip') as z:
        with z.open(f'pnp_dataset/{segment}_y.npy') as f:
            train_y = np.load(f)
            if limit is not None:
                train_y = train_y[:limit]
            for label in train_y:
                yield label

def build_dataset(segment: str, limit: Optional[int] = None, include_labels: bool = True) -> tf.data.Dataset:
    model_input = tf.TensorSpec(shape=(224, 224, 3), dtype=tf.float32)  # type: ignore
    model_output = tf.TensorSpec(shape=(), dtype=tf.int32)  # type: ignore

    def load():
        if include_labels:
            yield from zip(load_images(segment, limit), load_labels(segment, limit))
        else:
            yield from load_images(segment, limit)

    if include_labels:
        dataset_signature = (model_input, model_output)
    else:
        dataset_signature = model_input

    dataset = tf.data.Dataset.from_generator(load, output_signature=dataset_signature)
    return dataset