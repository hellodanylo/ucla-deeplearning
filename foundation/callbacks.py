from typing import Dict
import mlflow
from tensorflow.keras.callbacks import Callback


class MlflowCallback(Callback):
    def on_epoch_end(self, epoch: int, logs: Dict[str, float]):
        mlflow.log_metrics(metrics=logs, step=epoch)
