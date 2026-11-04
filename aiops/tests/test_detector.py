from app.config import MetricConfig
from app.detector import evaluate


def make_metric(**overrides: object) -> MetricConfig:
    values = {
        "id": "test_metric",
        "title": "Test metric",
        "source": "prometheus",
        "query": "up",
        "unit": "percent",
        "direction": "above",
        "warning_threshold": 80.0,
        "critical_threshold": 90.0,
        "z_threshold": 3.0,
        "critical_z_threshold": 4.5,
        "min_samples": None,
        "baseline_window": None,
        "consecutive_breaches": None,
        "cooldown_seconds": None,
        "enabled": True,
    }
    values.update(overrides)
    return MetricConfig(**values)


def features(z_score: float = 0.0, robust_z_score: float = 0.0) -> dict[str, float | int]:
    return {
        "samples": 10,
        "mean": 50.0,
        "std": 2.0,
        "median": 50.0,
        "mad": 1.0,
        "z_score": z_score,
        "robust_z_score": robust_z_score,
        "delta": 0.0,
        "min": 45.0,
        "max": 55.0,
        "slope": 0.0,
    }


def test_warming_up_until_minimum_samples() -> None:
    result = evaluate(make_metric(), 99.0, {**features(), "samples": 4}, 5)

    assert result.status == "warming_up"
    assert "baseline samples" in result.reasons[0]


def test_absolute_warning_threshold() -> None:
    result = evaluate(make_metric(), 85.0, features(), 5)

    assert result.status == "warning"
    assert "warning threshold" in result.reasons[0]


def test_absolute_critical_threshold() -> None:
    result = evaluate(make_metric(), 95.0, features(), 5)

    assert result.status == "critical"


def test_below_direction_critical_threshold() -> None:
    metric = make_metric(
        direction="below",
        warning_threshold=0.99,
        critical_threshold=0.5,
    )

    result = evaluate(metric, 0.0, features(), 5)

    assert result.status == "critical"


def test_z_score_warning_and_critical() -> None:
    warning = evaluate(make_metric(warning_threshold=None, critical_threshold=None), 50.0, features(3.2), 5)
    critical = evaluate(make_metric(warning_threshold=None, critical_threshold=None), 50.0, features(5.0), 5)

    assert warning.status == "warning"
    assert critical.status == "critical"


def test_normal_value() -> None:
    result = evaluate(make_metric(), 50.0, features(), 5)

    assert result.status == "ok"
    assert result.reasons == ()
