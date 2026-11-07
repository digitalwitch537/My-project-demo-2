from __future__ import annotations

import logging
from typing import Any

from .config import CorrelationConfig

logger = logging.getLogger(__name__)


def _severity_rank(status: str) -> int:
    return {"critical": 2, "warning": 1}.get(status, 0)


def _alert_sort_key(alert: dict[str, Any]) -> tuple[int, float, str]:
    features = alert.get("features") or {}
    try:
        z_score = abs(float(features.get("z_score", 0.0)))
    except (TypeError, ValueError):
        z_score = 0.0
    return (
        -_severity_rank(str(alert.get("status", ""))),
        -z_score,
        str(alert.get("metric", "")),
    )


class IncidentCorrelator:
    def __init__(self, config: CorrelationConfig) -> None:
        self.config = config

    def process(
        self,
        results: list[dict[str, Any]],
        state: dict[str, Any],
        timestamp: str,
        epoch: float,
    ) -> dict[str, Any] | None:
        correlation_state = state.setdefault("correlation", {})
        correlation_state.setdefault("active", None)
        active = correlation_state.get("active")
        candidate = correlation_state.get("candidate")
        qualifying = {
            str(result.get("metric")): result
            for result in results
            if result.get("breach_due")
        }

        if active:
            self._update_active(active, qualifying, correlation_state, timestamp, epoch)
            return None

        if candidate:
            candidate.setdefault("metrics", {}).update(qualifying)
            if qualifying:
                candidate["last_seen_epoch"] = epoch
            window_elapsed = (
                epoch - float(candidate.get("started_epoch", epoch))
            ) >= self.config.window_seconds
            if window_elapsed:
                return self._finish_candidate(candidate, correlation_state, timestamp, epoch)
            return None

        if qualifying:
            started_epoch = epoch
            correlation_state["candidate"] = {
                "id": f"incident-{int(started_epoch)}",
                "started_at": timestamp,
                "started_epoch": started_epoch,
                "last_seen_epoch": epoch,
                "metrics": qualifying,
            }
        return None

    def _update_active(
        self,
        active: dict[str, Any],
        qualifying: dict[str, dict[str, Any]],
        correlation_state: dict[str, Any],
        timestamp: str,
        epoch: float,
    ) -> None:
        if qualifying:
            active["last_seen_at"] = timestamp
            active["last_seen_epoch"] = epoch
            active.setdefault("metrics", {}).update(qualifying)
            return

        last_seen = float(active.get("last_seen_epoch", 0.0))
        if epoch - last_seen >= self.config.resolve_after_seconds:
            active["closed_at"] = active.get("last_seen_at") or timestamp
            active["closed_epoch"] = epoch
            correlation_state["active"] = None

    def _finish_candidate(
        self,
        candidate: dict[str, Any],
        correlation_state: dict[str, Any],
        timestamp: str,
        epoch: float,
    ) -> dict[str, Any] | None:
        metrics: dict[str, dict[str, Any]] = candidate.get("metrics") or {}
        alerts = sorted(metrics.values(), key=_alert_sort_key)
        has_critical = any(str(alert.get("status")) == "critical" for alert in alerts)
        enough_metrics = len(metrics) >= self.config.min_distinct_metrics
        critical_ok = has_critical or not self.config.require_critical

        correlation_state["candidate"] = None
        if not enough_metrics or not critical_ok:
            logger.info(
                "Correlated incident suppressed: %s distinct metrics, critical=%s",
                len(metrics),
                has_critical,
            )
            correlation_state["last_suppressed"] = {
                "at": timestamp,
                "epoch": epoch,
                "distinct_metrics": len(metrics),
                "metric_ids": sorted(metrics),
                "reason": "insufficient_metrics" if not enough_metrics else "critical_required",
            }
            return None

        selected = alerts[: max(1, self.config.max_related_metrics)]
        severity = "critical" if has_critical else "warning"
        incident = {
            "id": str(candidate.get("id") or f"incident-{int(epoch)}"),
            "started_at": str(candidate.get("started_at", timestamp)),
            "started_epoch": float(candidate.get("started_epoch", epoch)),
            "detected_at": timestamp,
            "detected_epoch": epoch,
            "window_seconds": self.config.window_seconds,
            "severity": severity,
            "metric_count": len(metrics),
            "alerts": selected,
            "omitted_count": max(0, len(metrics) - len(selected)),
            "alert_sent": False,
            "ai_model_triggered": False,
            "notified_at": None,
            "notified_epoch": None,
            "last_seen_at": timestamp,
            "last_seen_epoch": epoch,
        }
        correlation_state["active"] = incident
        return incident
