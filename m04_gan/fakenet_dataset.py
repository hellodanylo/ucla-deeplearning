import numpy as np
from PIL import Image
import tensorflow as tf
import pandas as pd


# See Python Generator
# https://peps.python.org/pep-0255/
def generator_score_single():
    metadata = pd.read_csv('fakenet_dataset/score/metadata.csv')
    
    for _, row in metadata.iterrows():
        image_a_path = 'fakenet_dataset/score/images/' + row['file_name_a']
        image_b_path = 'fakenet_dataset/score/images/' + row['file_name_b']

        image_a_np = np.array(Image.open(image_a_path))
        image_b_np = np.array(Image.open(image_b_path))

        model_input = image_a_np
        yield model_input

        # Uncomment if you want to compare the two images after inference
        # model_input = image_b_np
        # yield model_input


# See Tensorflow Dataset
# https://www.tensorflow.org/api_docs/python/tf/data/Dataset
def build_dataset_score_single() -> tf.data.Dataset:
    model_input = tf.TensorSpec(shape=(224, 224, 3), dtype=tf.float32)  # type: ignore

    dataset_signature = model_input

    dataset = tf.data.Dataset.from_generator(
        generator_score_single, 
        output_signature=dataset_signature
    )

    return dataset


# See Python Generator
# https://peps.python.org/pep-0255/
def build_generator_labeled_paired(metadata: pd.DataFrame):
    def generator():
        for _, row in metadata.iterrows():
            training_path = 'fakenet_dataset/train/images/' + row['file_name_training']
            generated_path = 'fakenet_dataset/train/images/' + row['file_name_generated']

            training_np = np.array(Image.open(training_path))
            generated_np = np.array(Image.open(generated_path))

            model_output = np.random.randint(low=0, high=2, size=1)

            if model_output == 1:
                model_input = (training_np, generated_np)
            else:
                model_input = (generated_np, training_np)

            yield (model_input, model_output)

    return generator


# See Tensorflow Dataset
# https://www.tensorflow.org/api_docs/python/tf/data/Dataset
def build_dataset_labeled_paired(metadata: pd.DataFrame):
    image_signature = tf.TensorSpec(shape=(224, 224, 3), dtype=tf.float32)  # type: ignore

    model_input = (image_signature, image_signature)
    model_output = tf.TensorSpec(shape=(1,), dtype=tf.int32)  # type: ignore

    dataset_signature = (model_input, model_output)

    dataset = tf.data.Dataset.from_generator(
        build_generator_labeled_paired(metadata), 
        output_signature=dataset_signature
    )

    return dataset


# See Python Generator
# https://peps.python.org/pep-0255/
def build_generator_labeled_single(metadata: pd.DataFrame):
    def generator():
        for _, row in metadata.iterrows():
            training_path = 'fakenet_dataset/train/images/' + row['file_name_training']
            generated_path = 'fakenet_dataset/train/images/' + row['file_name_generated']

            training_np = np.array(Image.open(training_path)).astype(np.float32)
            generated_np = np.array(Image.open(generated_path)).astype(np.float32)

            model_input = training_np
            model_output = (1,)
            yield (model_input, model_output)

            model_input = generated_np
            model_output = (0,)
            yield (model_input, model_output)
    return generator


# See Tensorflow Dataset
# https://www.tensorflow.org/api_docs/python/tf/data/Dataset
def build_dataset_labeled_single(metadata: pd.DataFrame) -> tf.data.Dataset:
    model_input = tf.TensorSpec(shape=(224, 224, 3), dtype=tf.float32)  # type: ignore
    model_output = tf.TensorSpec(shape=(1,), dtype=tf.int32)  # type: ignore

    dataset_signature = (model_input, model_output)

    dataset = tf.data.Dataset.from_generator(
        build_generator_labeled_single(metadata), 
        output_signature=dataset_signature
    )

    return dataset


# See Python Generator
# https://peps.python.org/pep-0255/
def generator_score_paired():
    metadata = pd.read_csv('fakenet_dataset/score/metadata.csv')

    for _, row in metadata.iterrows():
        image_a_path = 'fakenet_dataset/score/images/' + row['file_name_a']
        image_b_path = 'fakenet_dataset/score/images/' + row['file_name_b']

        image_a_np = np.array(Image.open(image_a_path))
        image_b_np = np.array(Image.open(image_b_path))

        model_input = (image_a_np, image_b_np)
        yield (model_input,)


# See Tensorflow Dataset
# https://www.tensorflow.org/api_docs/python/tf/data/Dataset
def build_dataset_score_paired():
    image_signature = tf.TensorSpec(shape=(224, 224, 3), dtype=tf.float32)  # type: ignore

    model_input = (image_signature, image_signature)

    dataset_signature = (model_input,)

    dataset = tf.data.Dataset.from_generator(
        generator_score_paired, 
        output_signature=dataset_signature
    )

    return dataset