from datetime import datetime, timedelta, timezone

from app.config import CorrelationConfig
from app.correlation import IncidentCorrelator


def make_config() -> CorrelationConfig:
    return CorrelationConfig(
        enabled=True,
        window_seconds=300,
        min_distinct_metrics=5,
        max_related_metrics=5,
        resolve_after_seconds=300,
        require_critical=False,
        suppress_single_alerts=True,
    )


def result(metric: str, status: str = "warning") -> dict:
    return {
        "metric": metric,
        "title": metric.replace("_", " ").title(),
        "status": status,
        "value": 10.0,
        "unit": "ops/s",
        "reasons": ["threshold crossed"],
        "features": {"z_score": 3.0},
        "breach_due": True,
    }


def timestamp(base: datetime, seconds: int) -> str:
    return (base + timedelta(seconds=seconds)).isoformat()


def test_incident_requires_five_metrics_and_window(tmp_path) -> None:
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    correlator = IncidentCorrelator(make_config())
    state: dict = {}

    for index in range(4):
        assert (
            correlator.process(
                [result(f"metric_{index}")],
                state,
                timestamp(base, index),
                float(index),
            )
            is None
        )

    assert (
        correlator.process(
            [result("metric_4", "critical")],
            state,
            timestamp(base, 299),
            299.0,
        )
        is None
    )

    incident = correlator.process([], state, timestamp(base, 300), 300.0)

    assert incident is not None
    assert incident["metric_count"] == 5
    assert incident["severity"] == "critical"
    assert len(incident["alerts"]) == 5
    assert incident["alerts"][0]["metric"] == "metric_4"
    assert state["correlation"]["active"] is incident


def test_incident_is_suppressed_with_fewer_than_five_metrics() -> None:
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    correlator = IncidentCorrelator(make_config())
    state: dict = {}

    correlator.process(
        [result(f"metric_{index}") for index in range(4)],
        state,
        timestamp(base, 0),
        0.0,
    )
    assert correlator.process([], state, timestamp(base, 300), 300.0) is None

    suppressed = state["correlation"]["last_suppressed"]
    assert suppressed["distinct_metrics"] == 4
    assert suppressed["reason"] == "insufficient_metrics"
    assert state["correlation"]["active"] is None


def test_active_incident_resolves_after_quiet_period() -> None:
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    correlator = IncidentCorrelator(make_config())
    state: dict = {}

    correlator.process(
        [result(f"metric_{index}") for index in range(5)],
        state,
        timestamp(base, 0),
        0.0,
    )
    incident = correlator.process([], state, timestamp(base, 300), 300.0)
    assert incident is not None

    assert correlator.process([], state, timestamp(base, 599), 599.0) is None
    assert state["correlation"]["active"] is incident

    assert correlator.process([], state, timestamp(base, 600), 600.0) is None
    assert state["correlation"]["active"] is None
    assert incident["closed_epoch"] == 600.0
