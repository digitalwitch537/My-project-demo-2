from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class SlackConfig:
    enabled: bool
    dry_run: bool
    webhook_url: str
    timeout_seconds: float
    channel: str


@dataclass(frozen=True)
class AiModelConfig:
    enabled: bool
    url: str
    timeout_seconds: float
    window_seconds: int


@dataclass(frozen=True)
class MetricConfig:
    id: str
    title: str
    source: str
    query: str
    unit: str
    direction: str
    warning_threshold: float | None
    critical_threshold: float | None
    z_threshold: float
    critical_z_threshold: float | None
    min_samples: int | None
    baseline_window: int | None
    consecutive_breaches: int | None
    cooldown_seconds: int | None
    enabled: bool


@dataclass(frozen=True)
class AppConfig:
    prometheus_url: str
    loki_url: str
    grafana_root_url: str
    data_dir: Path
    poll_interval_seconds: int
    history_size: int
    baseline_window: int
    min_samples: int
    consecutive_breaches: int
    cooldown_seconds: int
    request_timeout_seconds: float
    results_max_bytes: int
    anomalies_max_bytes: int
    slack: SlackConfig
    ai_model: AiModelConfig
    metrics: tuple[MetricConfig, ...]


def _as_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _metric_threshold(metric: dict[str, Any], key: str) -> float | None:
    return _optional_float(metric.get(key))


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    service = raw.get("service") or {}
    slack_raw = raw.get("slack") or {}

    data_dir_raw = os.getenv("AIOPS_DATA_DIR", raw.get("data_dir", "/app/data"))
    data_dir = Path(data_dir_raw)
    if not data_dir.is_absolute():
        data_dir = (config_path.parent / data_dir).resolve()

    metrics: list[MetricConfig] = []
    for item in raw.get("metrics") or []:
        source = str(item.get("source", "prometheus")).strip().lower()
        direction = str(item.get("direction", "both")).strip().lower()
        if source not in {"prometheus", "loki"}:
            raise ValueError(f"unsupported metric source: {source}")
        if direction not in {"above", "below", "both"}:
            raise ValueError(f"unsupported metric direction: {direction}")

        metrics.append(
            MetricConfig(
                id=str(item["id"]).strip(),
                title=str(item.get("title", item["id"])).strip(),
                source=source,
                query=str(item["query"]).strip(),
                unit=str(item.get("unit", "")).strip(),
                direction=direction,
                warning_threshold=_metric_threshold(item, "warning_threshold"),
                critical_threshold=_metric_threshold(item, "critical_threshold"),
                z_threshold=float(item.get("z_threshold", 3.0)),
                critical_z_threshold=_optional_float(item.get("critical_z_threshold")),
                min_samples=_optional_int(item.get("min_samples")),
                baseline_window=_optional_int(item.get("baseline_window")),
                consecutive_breaches=_optional_int(item.get("consecutive_breaches")),
                cooldown_seconds=_optional_int(item.get("cooldown_seconds")),
                enabled=_as_bool(item.get("enabled"), True),
            )
        )

    if not metrics:
        raise ValueError("config.yml must define at least one metric")

    slack = SlackConfig(
        enabled=_as_bool(slack_raw.get("enabled"), True),
        dry_run=_as_bool(
            os.getenv("SLACK_DRY_RUN"),
            _as_bool(slack_raw.get("dry_run"), False),
        ),
        webhook_url=os.getenv("SLACK_WEBHOOK_URL", str(slack_raw.get("webhook_url", ""))),
        timeout_seconds=float(
            os.getenv("SLACK_TIMEOUT_SECONDS", slack_raw.get("timeout_seconds", 10))
        ),
        channel=os.getenv("SLACK_CHANNEL", str(slack_raw.get("channel", ""))),
    )

    ai_model_raw = raw.get("ai_model") or {}
    ai_model = AiModelConfig(
        enabled=_as_bool(
            os.getenv("AI_MODEL_ENABLED"),
            _as_bool(ai_model_raw.get("enabled"), False),
        ),
        url=os.getenv(
            "AI_MODEL_URL", str(ai_model_raw.get("url", "http://ai-model:8090"))
        ).rstrip("/"),
        timeout_seconds=float(
            os.getenv(
                "AI_MODEL_TIMEOUT_SECONDS",
                ai_model_raw.get("timeout_seconds", 5),
            )
        ),
        window_seconds=int(
            os.getenv(
                "AI_MODEL_WINDOW_SECONDS",
                ai_model_raw.get("window_seconds", 360),
            )
        ),
    )

    return AppConfig(
        prometheus_url=os.getenv(
            "PROMETHEUS_URL", str(raw.get("prometheus_url", "http://prometheus:9090"))
        ).rstrip("/"),
        loki_url=os.getenv(
            "LOKI_URL", str(raw.get("loki_url", "http://loki:3100"))
        ).rstrip("/"),
        grafana_root_url=os.getenv(
            "GRAFANA_ROOT_URL", str(raw.get("grafana_root_url", ""))
        ).rstrip("/"),
        data_dir=data_dir,
        poll_interval_seconds=int(
            os.getenv("AIOPS_POLL_INTERVAL_SECONDS", service.get("poll_interval_seconds", 60))
        ),
        history_size=int(
            os.getenv("AIOPS_HISTORY_SIZE", service.get("history_size", 1440))
        ),
        baseline_window=int(
            os.getenv("AIOPS_BASELINE_WINDOW", service.get("baseline_window", 60))
        ),
        min_samples=int(os.getenv("AIOPS_MIN_SAMPLES", service.get("min_samples", 15))),
        consecutive_breaches=int(
            os.getenv(
                "AIOPS_CONSECUTIVE_BREACHES",
                service.get("consecutive_breaches", 2),
            )
        ),
        cooldown_seconds=int(
            os.getenv("AIOPS_COOLDOWN_SECONDS", service.get("cooldown_seconds", 900))
        ),
        request_timeout_seconds=float(
            os.getenv(
                "AIOPS_REQUEST_TIMEOUT_SECONDS",
                service.get("request_timeout_seconds", 10),
            )
        ),
        results_max_bytes=int(
            os.getenv(
                "AIOPS_RESULTS_MAX_BYTES",
                service.get("results_max_bytes", 5242880),
            )
        ),
        anomalies_max_bytes=int(
            os.getenv(
                "AIOPS_ANOMALIES_MAX_BYTES",
                service.get("anomalies_max_bytes", 5242880),
            )
        ),
        slack=slack,
        ai_model=ai_model,
        metrics=tuple(metrics),
    )
