import numpy as np
import pytest
from scipy import stats
from sklearn.metrics import r2_score
import tensorflow as tf

from baskerville.metrics import *

# data dimensions
N, L, T = 6, 8, 4


@pytest.fixture
def sample_data():
    y_true = tf.random.uniform((N, L, T), minval=0, maxval=10, dtype=tf.float32)
    y_pred = y_true + tf.random.normal((N, L, T), mean=0, stddev=0.1)
    return y_true, y_pred


def test_PearsonR(sample_data):
    y_true, y_pred = sample_data
    pearsonr = PearsonR(num_targets=T, summarize=False)
    pearsonr.update_state(y_true, y_pred)
    tf_result = pearsonr.result().numpy()

    # Compute SciPy result
    scipy_result = np.zeros(T)
    y_true_np = y_true.numpy().reshape(-1, T)
    y_pred_np = y_pred.numpy().reshape(-1, T)
    for i in range(T):
        scipy_result[i], _ = stats.pearsonr(y_true_np[:, i], y_pred_np[:, i])

    np.testing.assert_allclose(tf_result, scipy_result, rtol=1e-5, atol=1e-5)

    # Test summarized result
    pearsonr_summarized = PearsonR(num_targets=T, summarize=True)
    pearsonr_summarized.update_state(y_true, y_pred)
    tf_result_summarized = pearsonr_summarized.result().numpy()
    assert tf_result_summarized.shape == ()
    assert np.isclose(tf_result_summarized, np.mean(scipy_result), rtol=1e-5, atol=1e-5)


def test_R2(sample_data):
    y_true, y_pred = sample_data
    r2 = R2(num_targets=T, summarize=False)
    r2.update_state(y_true, y_pred)
    tf_result = r2.result().numpy()

    # Compute sklearn result
    sklearn_result = np.zeros(T)
    y_true_np = y_true.numpy().reshape(-1, T)
    y_pred_np = y_pred.numpy().reshape(-1, T)
    for i in range(T):
        sklearn_result[i] = r2_score(y_true_np[:, i], y_pred_np[:, i])

    np.testing.assert_allclose(tf_result, sklearn_result, rtol=1e-5, atol=1e-5)

    # Test summarized result
    r2_summarized = R2(num_targets=T, summarize=True)
    r2_summarized.update_state(y_true, y_pred)
    tf_result_summarized = r2_summarized.result().numpy()
    assert tf_result_summarized.shape == ()
    assert np.isclose(
        tf_result_summarized, np.mean(sklearn_result), rtol=1e-5, atol=1e-5
    )


def test_poisson_multinomial_shape(sample_data):
    y_true, y_pred = sample_data
    loss = poisson_multinomial(y_true, y_pred)
    assert loss.shape == (N, T)
