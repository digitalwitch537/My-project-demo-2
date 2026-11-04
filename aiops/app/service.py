from __future__ import annotations

import logging
import math
import threading
import time
from datetime import datetime, timezone
from typing import Any

from .clients import LokiClient, PrometheusClient, Sample
from .config import AppConfig, MetricConfig
from .detector import evaluate
from .features import compute_features
from .notifier import SlackNotifier
from .storage import JsonlWriter, StateStore, write_json_atomic

logger = logging.getLogger(__name__)


class AiopsService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.prometheus = PrometheusClient(
            config.prometheus_url,
            config.request_timeout_seconds,
        )
        self.loki = LokiClient(
            config.loki_url,
            config.request_timeout_seconds,
        )
        self.state_store = StateStore(config.data_dir / "state.json")
        self.results_writer = JsonlWriter(
            config.data_dir / "results.jsonl",
            config.results_max_bytes,
        )
        self.anomalies_writer = JsonlWriter(
            config.data_dir / "anomalies.jsonl",
            config.anomalies_max_bytes,
        )
        self.notifier = SlackNotifier(
            webhook_url=config.slack.webhook_url,
            dry_run=config.slack.dry_run,
            timeout_seconds=config.slack.timeout_seconds,
            channel=config.slack.channel,
            grafana_root_url=config.grafana_root_url,
        )
        self.state = self.state_store.load()
        self.stop_event = threading.Event()

    def run_forever(self) -> None:
        logger.info(
            "AIOps service started: poll=%ss metrics=%s data_dir=%s",
            self.config.poll_interval_seconds,
            len(self.config.metrics),
            self.config.data_dir,
        )
        while not self.stop_event.is_set():
            started = time.monotonic()
            try:
                self.run_once()
            except Exception:
                logger.exception("AIOps cycle failed")

            elapsed = time.monotonic() - started
            delay = max(0.0, self.config.poll_interval_seconds - elapsed)
            logger.info("Next anomaly check in %.1f seconds", delay)
            self.stop_event.wait(delay)
        logger.info("AIOps service stopped")

    def stop(self) -> None:
        self.stop_event.set()

    def run_once(self, now: datetime | None = None) -> list[dict[str, Any]]:
        if now is None:
            now = datetime.now(timezone.utc)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        timestamp = now.isoformat()
        epoch = now.timestamp()
        results: list[dict[str, Any]] = []

        for metric in self.config.metrics:
            if not metric.enabled:
                continue
            try:
                result = self._evaluate_metric(metric, timestamp, epoch)
            except Exception as exc:
                logger.exception("Metric evaluation failed: %s", metric.id)
                result = {
                    "timestamp": timestamp,
                    "metric": metric.id,
                    "title": metric.title,
                    "source": metric.source,
                    "status": "error",
                    "error": str(exc),
                }

            self.results_writer.append(result)
            if result.get("status") in {"warning", "critical"}:
                self.anomalies_writer.append(result)
            results.append(result)

        self.state["updated_at"] = timestamp
        self.state_store.save(self.state)

        write_json_atomic(
            self.config.data_dir / "latest.json",
            {"updated_at": timestamp, "results": results},
        )
        write_json_atomic(
            self.config.data_dir / "heartbeat.json",
            {
                "last_run": timestamp,
                "last_run_epoch": epoch,
                "poll_interval_seconds": self.config.poll_interval_seconds,
                "metrics": len(results),
            },
        )

        return results

    def _evaluate_metric(
        self,
        metric: MetricConfig,
        timestamp: str,
        epoch: float,
    ) -> dict[str, Any]:
        metric_state = self._metric_state(metric.id)
        history = metric_state["history"]
        history_values = self._history_values(history)

        try:
            sample = self._query(metric, epoch)
        except Exception as exc:
            metric_state["consecutive_breaches"] = 0
            return self._base_result(metric, timestamp, status="error", error=str(exc))

        if sample is None or not math.isfinite(sample.value):
            metric_state["consecutive_breaches"] = 0
            return self._base_result(
                metric,
                timestamp,
                status="no_data",
                reason="query returned no finite value",
            )

        baseline_window = metric.baseline_window or self.config.baseline_window
        min_samples = metric.min_samples or self.config.min_samples
        features = compute_features(history_values, sample.value, baseline_window)
        evaluation = evaluate(metric, sample.value, features, min_samples)

        consecutive = 0
        if evaluation.status in {"warning", "critical"}:
            consecutive = int(metric_state.get("consecutive_breaches", 0)) + 1
        metric_state["consecutive_breaches"] = consecutive

        required_breaches = max(
            1,
            metric.consecutive_breaches
            if metric.consecutive_breaches is not None
            else self.config.consecutive_breaches,
        )
        cooldown_seconds = max(
            0,
            metric.cooldown_seconds
            if metric.cooldown_seconds is not None
            else self.config.cooldown_seconds,
        )

        result = self._base_result(
            metric,
            timestamp,
            status=evaluation.status,
            value=sample.value,
            features=features,
            reasons=list(evaluation.reasons),
            labels=sample.labels,
        )
        result["consecutive_breaches"] = consecutive
        result["required_breaches"] = required_breaches

        alert_due = False
        alert_sent = False
        if evaluation.status in {"warning", "critical"} and consecutive >= required_breaches:
            last_attempt = float(metric_state.get("last_alert_attempt_epoch") or 0.0)
            last_success = float(metric_state.get("last_alert_epoch") or 0.0)
            last_activity = max(last_attempt, last_success)
            cooldown_elapsed = (epoch - last_activity) >= cooldown_seconds
            critical_upgrade = (
                evaluation.status == "critical"
                and metric_state.get("last_alert_level") != "critical"
                and metric_state.get("last_alert_attempt_level") != "critical"
            )
            alert_due = cooldown_elapsed or critical_upgrade

        if alert_due:
            if self.config.slack.enabled:
                alert_sent = self.notifier.send(metric, result)
            else:
                logger.info("Slack is disabled; suppressed alert for %s", metric.id)

            metric_state["last_alert_attempt_epoch"] = epoch
            metric_state["last_alert_attempt_level"] = evaluation.status
            if alert_sent:
                metric_state["last_alert_at"] = timestamp
                metric_state["last_alert_epoch"] = epoch
                metric_state["last_alert_level"] = evaluation.status

        result["alert_due"] = alert_due
        result["alert_sent"] = alert_sent
        result["thresholds"] = {
            "direction": metric.direction,
            "warning": metric.warning_threshold,
            "critical": metric.critical_threshold,
            "z": metric.z_threshold,
            "critical_z": metric.critical_z_threshold
            if metric.critical_z_threshold is not None
            else metric.z_threshold * 1.5,
        }

        history.append({"timestamp": timestamp, "epoch": epoch, "value": sample.value})
        if len(history) > self.config.history_size:
            del history[: len(history) - self.config.history_size]

        return result

    def _query(self, metric: MetricConfig, epoch: float) -> Sample | None:
        if metric.source == "prometheus":
            return self.prometheus.query(metric.query, at=epoch)
        if metric.source == "loki":
            return self.loki.query(metric.query, at=epoch)
        raise ValueError(f"unsupported metric source: {metric.source}")

    def _metric_state(self, metric_id: str) -> dict[str, Any]:
        metrics = self.state.setdefault("metrics", {})
        metric_state = metrics.setdefault(metric_id, {})
        metric_state.setdefault("history", [])
        metric_state.setdefault("consecutive_breaches", 0)
        metric_state.setdefault("last_alert_at", None)
        metric_state.setdefault("last_alert_epoch", 0.0)
        metric_state.setdefault("last_alert_attempt_epoch", 0.0)
        metric_state.setdefault("last_alert_attempt_level", None)
        metric_state.setdefault("last_alert_level", None)
        return metric_state

    def _history_values(self, history: list[dict[str, Any]]) -> list[float]:
        values: list[float] = []
        for item in history:
            try:
                value = float(item.get("value"))
            except (TypeError, ValueError):
                continue
            if math.isfinite(value):
                values.append(value)
        return values

    def _base_result(
        self,
        metric: MetricConfig,
        timestamp: str,
        status: str,
        value: float | None = None,
        features: dict[str, float | int] | None = None,
        reasons: list[str] | None = None,
        labels: dict[str, str] | None = None,
        reason: str | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "timestamp": timestamp,
            "metric": metric.id,
            "title": metric.title,
            "source": metric.source,
            "unit": metric.unit,
            "status": status,
        }
        if value is not None:
            result["value"] = value
        if features is not None:
            result["features"] = features
        if reasons:
            result["reasons"] = reasons
        if reason:
            result["reason"] = reason
        if labels:
            result["labels"] = labels
        if error:
            result["error"] = error
        return result
