import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from tensorflow.python.keras import backend as K

from statsmodels.regression.linear_model import OLS
import sklearn.metrics as metrics

from collections import OrderedDict

def r2_score(y_true, y_pred):
    SS_res =  K.sum(K.square(y_true - y_pred))
    SS_tot = K.sum(K.square(y_true - K.mean(y_true)))
    return 1 - SS_res/(SS_tot + K.epsilon())


def mean_error(y_true, y_pred):
    return K.mean(y_pred) - K.mean(y_true)


def nd_target_like_panel(
        like_panel: pd.DataFrame,
        target_nd: np.ndarray,
):
    like_panel = like_panel[['temperature']]

    target_nd = target_nd.ravel()
    target_panel = pd.DataFrame(
        target_nd,
        index=like_panel.index,
        columns=like_panel.columns
    )

    return target_panel


def plot_random_forecasts(past, future, forecast):
    cols = 3
    rows = 3

    samples = np.random.choice(
        past.index.levels[0],
        cols * rows,
        replace=False
    )

    plt.figure(figsize=[8 * cols, 8 * rows])
    for idx in range(cols * rows):
        sample = samples[idx]
        ax = plt.subplot(rows, cols, idx + 1)
        plt.title(sample)
        past.loc[sample].plot(ax=ax, color='blue', label='past')
        future.loc[sample].plot(ax=ax, color='green', label='future')
        forecast.loc[sample].plot(ax=ax, color='red', label='forecast')
        plt.legend()
    plt.tight_layout()
    
    
class Segment:
    def __init__(self, segment_name):
        self.segment_name = segment_name
        self.frames = {}


    def __getitem__(self, item):
        return self.frames[item]


    def __setitem__(self, key, value):
        self.frames[key] = value


    def to_pq_workdir(self, workdir):
        for name, frame in self.frames.items():
            filename = f'{self.segment_name}_{name}.parquet'
            self.frames[name].to_parquet(f'{workdir}/{filename}')


    @classmethod
    def from_pq_workdir(cls, workdir, segment_name, frame_names):
        """
        :param workdir:
        :return:
        """
        segment = cls(segment_name)

        for frame_name in frame_names:
            filename = f'{segment_name}_{frame_name}.parquet'
            segment.frames[frame_name] = pd.read_parquet(f'{workdir}/{filename}')

        return segment

    
class FeatureSegment(Segment):
    @classmethod
    def from_pq_workdir(cls, workdir, segment_name):
        frame_names = ['x']
        return Segment.from_pq_workdir(workdir, segment_name, frame_names)


class TargetSegment(Segment):
    @classmethod
    def from_pq_workdir(cls, workdir, segment_name):
        frame_names = ['y']
        return Segment.from_pq_workdir(workdir, segment_name, frame_names)


class RegressionSegment(Segment):
    @classmethod
    def from_pq_workdir(cls, workdir, segment_name):
        frame_names = ['x', 'y']
        return Segment.from_pq_workdir(workdir, segment_name, frame_names)


class SegmentDataset:
    def __init__(self):
        self.segments: typing.OrderedDict[str, Segment] = OrderedDict()


    def __getitem__(self, item):
        return self.segments[item]


    def __setitem__(self, key, value):
        self.segments[key] = value

    def to_pq_workdir(self, workdir):
        for segment in self.segments.values():
            segment.to_pq_workdir(workdir)


    @classmethod
    def from_pq_workdir(cls, workdir, segment_names, frame_names):
        dataset = cls()

        for name in segment_names:
            dataset[name] = Segment.from_pq_workdir(workdir, name, frame_names)

        return dataset


def forecast_mean(
        dataset: SegmentDataset,
        prediction_window
) -> SegmentDataset:
    mean_target_hat = SegmentDataset()
    for name, segment in dataset.segments.items():
        segment_features = segment['x']['temperature']
        segment_target_hat = predict_mean(segment_features, prediction_window)
        segment_target_hat.index = segment['y'].index

        mean_target_hat[name] = TargetSegment(name)
        mean_target_hat[name]['y'] = segment_target_hat

    return mean_target_hat


def forecast_constant(
        dataset: SegmentDataset,
        prediction_window
) -> SegmentDataset:
    const_target_hat = SegmentDataset()
    for name, segment in dataset.segments.items():
        segment_features = segment['x']['temperature']
        segment_target_hat = predict_constant(segment_features)
        segment_target_hat.index = segment['y'].index

        const_target_hat[name] = TargetSegment(name)
        const_target_hat[name]['y'] = segment_target_hat

    return const_target_hat


def predict_mean(lags, prediction_window):
    means = lags.groupby('sample').mean().values.reshape(-1, 1)
    means = np.repeat(means, prediction_window, -1).ravel()
    return pd.Series(means, index=lags.index, name=lags.name).reset_index(level=1, drop=True)


def predict_constant(lags):
    return lags.reset_index(level=1, drop=True)


def forecast_regression(
        dataset: SegmentDataset,
        prediction_window
) -> SegmentDataset:
    reg_features = to_regression_shape(
        dataset['train']['x'],
        prediction_window
    )

    reg_features['const'] = 1

    reg_target = to_regression_shape(
        dataset['train']['y'][['temperature']],
        prediction_window
    )

    reg_target_hat = SegmentDataset()

    models = [
        OLS(reg_target[target_name], reg_features).fit()
        for target_name in reg_target.columns
    ]

    for name, segment in dataset.segments.items():
        segment_features = segment['x']
        segment_features = to_regression_shape(segment_features, prediction_window)
        segment_features['const'] = 1

        segment_target_hat = [
            result.predict(segment_features)
            for result in models
        ]

        segment_target_hat = pd.concat(segment_target_hat, axis=1)
        segment_target_hat.columns = reg_target.columns
        segment_target_hat = to_panel_shape(segment_target_hat)['temperature']
        segment_target_hat.index = segment['y'].index

        reg_target_hat[name] = TargetSegment(name)
        reg_target_hat[name]['y'] = segment_target_hat


    return reg_target_hat


def compare_datasets(
        target_dataset: SegmentDataset,
        target_hat_datasets,
) -> pd.DataFrame:
    scores_by_segment = []

    for segment_name, segment in target_dataset.segments.items():
        segment_target = segment['y']['temperature']

        scores_by_model = []
        for model_name, target_hat_dataset in target_hat_datasets.items():
            target_hat = target_hat_dataset[segment_name]['y']
            scores = evaluate_forecast(segment_target, target_hat, model_name)
            scores_by_model.append(scores)

        scores_by_segment.append(
            pd.concat(scores_by_model, axis=0).round(2)
        )

    return pd.concat(
        scores_by_segment,
        axis=1,
        keys=list(target_dataset.segments.keys())
    )


def evaluate_forecast(y, y_hat, name):
    return pd.DataFrame({
        'ME' : y.mean() - y_hat.mean(),
        'MSE': metrics.mean_squared_error(y, y_hat),
        'MAE': metrics.mean_absolute_error(y, y_hat),
        'R2' : metrics.r2_score(y, y_hat)
    }, index=[name])


def evaluate_forecasts(future, forecasts):
    metrics_by_sample = pd.concat([
        evaluate_forecast(
            future.loc[sample],
            forecasts.loc[sample],
            sample
        )
        for sample in forecasts.index.levels[0]
    ])
    return metrics_by_sample


def to_regression_shape(panel, sequence_length):
    # timer is a repetitive 0, 1, ..., S array
    # that counts the time step within each sequence
    timer = np.arange(0, sequence_length).reshape(-1, sequence_length)
    timer = np.repeat(timer, panel.shape[0] / sequence_length, 0).ravel()

    tf = panel.reset_index('time')
    tf['time'] = timer
    tf = tf.set_index('time', append=True).unstack('time')

    return tf


def to_panel_shape(reg):
    return reg.stack('time')


def baseline_metrics(panel_dataset):
    prediction_window = panel_dataset['train']['y'].groupby('sample').size().max()
    
    models = {
        'mean': forecast_mean,
        'constant': forecast_constant,
        'regression': forecast_regression
    }

    models = {
        name: fun(panel_dataset, prediction_window)
        for name, fun in models.items()
    }

    return compare_datasets(panel_dataset, models)