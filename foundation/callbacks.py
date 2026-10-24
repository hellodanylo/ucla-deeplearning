from typing import Dict, Optional
import mlflow
from keras.callbacks import Callback


class MlflowCallback(Callback):
    def on_epoch_end(self, epoch: int, logs: Optional[Dict[str, float]] = None):
        mlflow.log_metrics(metrics=logs or {}, step=epoch)
