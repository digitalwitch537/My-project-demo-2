from pathlib import Path

import pytest

from app.config import (
    AppConfig,
    CollectionConfig,
    OllamaConfig,
    SlackConfig,
)


@pytest.fixture
def config(tmp_path: Path) -> AppConfig:
    return AppConfig(
        prometheus_url="http://prometheus:9090",
        loki_url="http://loki:3100",
        grafana_root_url="http://grafana:3000",
        data_dir=tmp_path,
        host="127.0.0.1",
        port=8090,
        worker_poll_seconds=0.01,
        collection=CollectionConfig(
            window_seconds=360,
            step_seconds=15,
            request_timeout_seconds=1.0,
            max_metric_points=12,
            max_log_lines=10,
            max_log_chars=2000,
            max_log_line_chars=300,
            log_queries=('{job="docker"}',),
        ),
        ollama=OllamaConfig(
            url="http://ollama:11434",
            model="gemma3:4b",
            timeout_seconds=1.0,
            num_ctx=1024,
            num_predict=100,
            temperature=0.1,
            keep_alive="5m",
        ),
        slack=SlackConfig(
            enabled=True,
            dry_run=True,
            webhook_url="",
            timeout_seconds=1.0,
            channel="",
        ),
    )


@pytest.fixture
def alert_payload() -> dict:
    return {
        "event_id": "api_5xx_rate:1700000000:critical",
        "triggered_at": "2026-01-01T00:06:00+00:00",
        "window_seconds": 360,
        "metric": {
            "id": "api_5xx_rate",
            "title": "API 5xx rate",
            "source": "prometheus",
            "query": "sum(rate(http_requests_total[5m]))",
            "unit": "req/s",
        },
        "result": {
            "status": "critical",
            "value": 12.0,
            "reasons": ["value crossed critical threshold"],
        },
        "related_metrics": [
            {
                "id": "api_5xx_rate",
                "title": "API 5xx rate",
                "source": "prometheus",
                "query": "sum(rate(http_requests_total[5m]))",
                "unit": "req/s",
            }
        ],
    }
