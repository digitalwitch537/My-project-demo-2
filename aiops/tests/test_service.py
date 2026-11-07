import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.clients import Sample
from app.config import (
    AiModelConfig,
    AppConfig,
    CorrelationConfig,
    MetricConfig,
    SlackConfig,
)
from app.service import AiopsService


class FakePrometheus:
    def __init__(self, values: list[float]) -> None:
        self.values = list(values)

    def query(self, expr: str, at: float | None = None) -> Sample:
        return Sample(value=self.values.pop(0), labels={"job": "mern-backend"})


def make_config(tmp_path: Path) -> AppConfig:
    metric = MetricConfig(
        id="api_request_rate",
        title="API request rate",
        source="prometheus",
        query="sum(rate(http_requests_total[5m]))",
        unit="req/s",
        direction="both",
        warning_threshold=None,
        critical_threshold=None,
        z_threshold=3.0,
        critical_z_threshold=4.5,
        min_samples=2,
        baseline_window=5,
        consecutive_breaches=1,
        cooldown_seconds=0,
        enabled=True,
    )
    return AppConfig(
        prometheus_url="http://prometheus:9090",
        loki_url="http://loki:3100",
        grafana_root_url="",
        data_dir=tmp_path,
        poll_interval_seconds=60,
        history_size=10,
        baseline_window=5,
        min_samples=2,
        consecutive_breaches=1,
        cooldown_seconds=0,
        request_timeout_seconds=1.0,
        results_max_bytes=1024 * 1024,
        anomalies_max_bytes=1024 * 1024,
        incidents_max_bytes=1024 * 1024,
        slack=SlackConfig(
            enabled=True,
            dry_run=True,
            webhook_url="",
            timeout_seconds=1.0,
            channel="",
        ),
        ai_model=AiModelConfig(
            enabled=True,
            url="http://ai-model:8090",
            timeout_seconds=1.0,
            window_seconds=900,
        ),
        correlation=CorrelationConfig(
            enabled=False,
            window_seconds=300,
            min_distinct_metrics=5,
            max_related_metrics=5,
            resolve_after_seconds=300,
            require_critical=False,
            suppress_single_alerts=True,
        ),
        metrics=(metric,),
    )


class FakeAiModel:
    def __init__(self) -> None:
        self.payloads: list[dict] = []

    def trigger(self, payload: dict) -> bool:
        self.payloads.append(payload)
        return True


def test_service_warms_up_then_alerts_and_persists(tmp_path: Path) -> None:
    service = AiopsService(make_config(tmp_path))
    service.prometheus = FakePrometheus([1.0, 2.0, 3.0])
    fake_ai_model = FakeAiModel()
    service.ai_model = fake_ai_model
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    first = service.run_once(start)
    second = service.run_once(start + timedelta(minutes=1))
    third = service.run_once(start + timedelta(minutes=2))

    assert first[0]["status"] == "warming_up"
    assert second[0]["status"] == "warming_up"
    assert third[0]["status"] == "warning"
    assert third[0]["alert_sent"] is True
    assert third[0]["ai_model_triggered"] is True
    assert third[0]["features"]["z_score"] == pytest.approx(3.0)
    assert len(fake_ai_model.payloads) == 1
    assert fake_ai_model.payloads[0]["event_id"].startswith("api_request_rate:")
    assert fake_ai_model.payloads[0]["related_metrics"][0]["id"] == "api_request_rate"

    assert len((tmp_path / "results.jsonl").read_text(encoding="utf-8").splitlines()) == 3
    assert len((tmp_path / "anomalies.jsonl").read_text(encoding="utf-8").splitlines()) == 1

    state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    metric_state = state["metrics"]["api_request_rate"]
    assert len(metric_state["history"]) == 3
    assert metric_state["consecutive_breaches"] == 1
    assert (tmp_path / "latest.json").exists()
    assert (tmp_path / "heartbeat.json").exists()


def test_service_records_no_data(tmp_path: Path) -> None:
    service = AiopsService(make_config(tmp_path))
    service.prometheus.query = lambda expr, at=None: None

    results = service.run_once(datetime(2026, 1, 1, tzinfo=timezone.utc))

    assert results[0]["status"] == "no_data"
    assert not (tmp_path / "anomalies.jsonl").exists()


def _correlated_config(tmp_path: Path) -> AppConfig:
    base = make_config(tmp_path)
    metrics = tuple(
        replace(base.metrics[0], id=f"metric_{index}", title=f"Metric {index}")
        for index in range(5)
    )
    return replace(
        base,
        metrics=metrics,
        correlation=replace(base.correlation, enabled=True),
    )


def test_service_emits_one_correlated_incident_after_window(tmp_path: Path) -> None:
    service = AiopsService(_correlated_config(tmp_path))
    values = []
    baseline = [1.0, 2.0]
    for run in range(8):
        for _ in range(5):
            values.append(baseline[run] if run < 2 else 10.0)
    service.prometheus = FakePrometheus(values)
    fake_ai_model = FakeAiModel()
    service.ai_model = fake_ai_model
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    previous = None
    for minute in range(8):
        previous = service.run_once(start + timedelta(minutes=minute))

    latest = json.loads((tmp_path / "latest.json").read_text(encoding="utf-8"))
    incident = latest["incident"]

    assert incident["metric_count"] == 5
    assert len(incident["alerts"]) == 5
    assert incident["alert_sent"] is True
    assert incident["ai_model_triggered"] is True
    assert all(result["correlated"] is True for result in previous)
    assert all(result["alert_sent"] is True for result in previous)
    assert len(fake_ai_model.payloads) == 1
    payload = fake_ai_model.payloads[0]
    assert payload["event_id"].startswith("incident:")
    assert payload["incident"]["id"] == incident["id"]
    assert len(payload["incident"]["alerts"]) == 5
    assert len(payload["related_metrics"]) == 5

    incidents = (tmp_path / "incidents.jsonl").read_text(encoding="utf-8")
    assert len(incidents.splitlines()) == 1
    assert json.loads(incidents.splitlines()[0])["id"] == incident["id"]
