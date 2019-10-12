from tensorflow.python.keras import backend as K


def r2_score(y_true, y_pred):
    SS_res =  K.sum(K.square(y_true - y_pred))
    SS_tot = K.sum(K.square(y_true - K.mean(y_true)))
    return 1 - SS_res/(SS_tot + K.epsilon())


def mean_error(y_true, y_pred):
    return K.mean(y_pred) - K.mean(y_true)