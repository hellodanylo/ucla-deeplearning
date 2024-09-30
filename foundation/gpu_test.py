import numpy as np

from keras import layers, models


def get_model(n_inputs: int) -> models.Model:
    inp = layers.Input(shape=(n_inputs,))

    out = layers.Dense(n_inputs, activation="linear")(inp)
    m = models.Model(inputs=inp, outputs=out)
    m.compile(loss="mse", optimizer="adam")
    m.summary()
    return m


def main(big: bool):
    model = get_model(4096)

    N = 1_000_000 if big else 1_000
    train_data = np.zeros((N, 4096), dtype=np.float32)
    print(
        f"Evaluating on {train_data.shape[0]} data points and {train_data.nbytes / 1024**2} MiB."
    )

    with tf.device("/CPU:0"):
        train_data = tf.constant(train_data)
        model.predict(train_data, batch_size=16, verbose=1)
        model.fit(
            train_data, train_data, epochs=3, verbose=1, batch_size=16, max_queue_size=1
        )


import tensorflow as tf

gpus = tf.config.experimental.list_physical_devices("GPU")
tf.config.experimental.set_memory_growth(gpus[0], True)
# tf.debugging.set_log_device_placement(True)

main(True)
