from math import sqrt

import pytest

from app.features import compute_features


def test_compute_features_on_rolling_window() -> None:
    features = compute_features([1, 2, 3, 4, 5], 6, 5)

    assert features["samples"] == 5
    assert features["mean"] == pytest.approx(3.0)
    assert features["std"] == pytest.approx(sqrt(2))
    assert features["median"] == pytest.approx(3.0)
    assert features["mad"] == pytest.approx(1.0)
    assert features["z_score"] == pytest.approx(3 / sqrt(2))
    assert features["robust_z_score"] == pytest.approx(0.6745 * 3)
    assert features["delta"] == pytest.approx(1.0)
    assert features["min"] == pytest.approx(1.0)
    assert features["max"] == pytest.approx(5.0)
    assert features["slope"] == pytest.approx(1.0)


def test_compute_features_with_empty_history() -> None:
    features = compute_features([], 10, 60)

    assert features["samples"] == 0
    assert features["z_score"] == 0.0
    assert features["robust_z_score"] == 0.0
