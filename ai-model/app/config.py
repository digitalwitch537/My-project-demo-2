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
class OllamaConfig:
    url: str
    model: str
    timeout_seconds: float
    num_ctx: int
    num_predict: int
    temperature: float
    keep_alive: str


@dataclass(frozen=True)
class CollectionConfig:
    window_seconds: int
    step_seconds: int
    request_timeout_seconds: float
    max_metric_points: int
    max_log_lines: int
    max_log_chars: int
    max_log_line_chars: int
    log_queries: tuple[str, ...]


@dataclass(frozen=True)
class AppConfig:
    prometheus_url: str
    loki_url: str
    grafana_root_url: str
    data_dir: Path
    host: str
    port: int
    worker_poll_seconds: float
    collection: CollectionConfig
    ollama: OllamaConfig
    slack: SlackConfig


def _as_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    server = raw.get("server") or {}
    worker = raw.get("worker") or {}
    collection = raw.get("collection") or {}
    ollama = raw.get("ollama") or {}
    slack = raw.get("slack") or {}

    data_dir_raw = os.getenv("AI_MODEL_DATA_DIR", raw.get("data_dir", "/app/data"))
    data_dir = Path(data_dir_raw)
    if not data_dir.is_absolute():
        data_dir = (config_path.parent / data_dir).resolve()

    log_queries = collection.get("log_queries") or [
        '{job="docker"}',
        '{job="system"}',
    ]

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
        host=os.getenv("AI_MODEL_HOST", str(server.get("host", "0.0.0.0"))),
        port=int(os.getenv("AI_MODEL_PORT", server.get("port", 8090))),
        worker_poll_seconds=float(
            os.getenv("AI_MODEL_WORKER_POLL_SECONDS", worker.get("poll_seconds", 1.0))
        ),
        collection=CollectionConfig(
            window_seconds=int(
                os.getenv(
                    "AI_MODEL_WINDOW_SECONDS",
                    collection.get("window_seconds", 900),
                )
            ),
            step_seconds=int(
                os.getenv("AI_MODEL_STEP_SECONDS", collection.get("step_seconds", 15))
            ),
            request_timeout_seconds=float(
                os.getenv(
                    "AI_MODEL_COLLECTION_TIMEOUT_SECONDS",
                    collection.get("request_timeout_seconds", 15),
                )
            ),
            max_metric_points=int(
                os.getenv(
                    "AI_MODEL_MAX_METRIC_POINTS",
                    collection.get("max_metric_points", 20),
                )
            ),
            max_log_lines=int(
                os.getenv("AI_MODEL_MAX_LOG_LINES", collection.get("max_log_lines", 600))
            ),
            max_log_chars=int(
                os.getenv("AI_MODEL_MAX_LOG_CHARS", collection.get("max_log_chars", 30000))
            ),
            max_log_line_chars=int(
                os.getenv(
                    "AI_MODEL_MAX_LOG_LINE_CHARS",
                    collection.get("max_log_line_chars", 1200),
                )
            ),
            log_queries=tuple(str(query).strip() for query in log_queries if str(query).strip()),
        ),
        ollama=OllamaConfig(
            url=os.getenv(
                "OLLAMA_URL", str(ollama.get("url", "http://ollama:11434"))
            ).rstrip("/"),
            model=os.getenv("OLLAMA_MODEL", str(ollama.get("model", "gemma3:4b"))),
            timeout_seconds=float(
                os.getenv(
                    "OLLAMA_TIMEOUT_SECONDS",
                    ollama.get("timeout_seconds", 300),
                )
            ),
            num_ctx=int(os.getenv("OLLAMA_NUM_CTX", ollama.get("num_ctx", 20480))),
            num_predict=int(
                os.getenv("OLLAMA_NUM_PREDICT", ollama.get("num_predict", 1200))
            ),
            temperature=float(
                os.getenv("OLLAMA_TEMPERATURE", ollama.get("temperature", 0.1))
            ),
            keep_alive=os.getenv(
                "OLLAMA_KEEP_ALIVE", str(ollama.get("keep_alive", "5m"))
            ),
        ),
        slack=SlackConfig(
            enabled=_as_bool(
                os.getenv("SLACK_ENABLED"),
                _as_bool(slack.get("enabled"), True),
            ),
            dry_run=_as_bool(
                os.getenv("SLACK_DRY_RUN"),
                _as_bool(slack.get("dry_run"), False),
            ),
            webhook_url=os.getenv(
                "SLACK_WEBHOOK_URL", str(slack.get("webhook_url", ""))
            ),
            timeout_seconds=float(
                os.getenv(
                    "SLACK_TIMEOUT_SECONDS",
                    slack.get("timeout_seconds", 10),
                )
            ),
            channel=os.getenv("SLACK_CHANNEL", str(slack.get("channel", ""))),
        ),
    )
