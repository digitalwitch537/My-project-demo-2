from __future__ import annotations

import logging
from typing import Any

import requests

from .config import MetricConfig

logger = logging.getLogger(__name__)


class SlackNotifier:
    def __init__(
        self,
        webhook_url: str,
        dry_run: bool,
        timeout_seconds: float,
        channel: str,
        grafana_root_url: str,
        session: requests.Session | None = None,
    ) -> None:
        self.webhook_url = webhook_url
        self.dry_run = dry_run
        self.timeout_seconds = timeout_seconds
        self.channel = channel
        self.grafana_root_url = grafana_root_url.rstrip("/")
        self.session = session or requests.Session()

    def send(self, metric: MetricConfig, result: dict[str, Any]) -> bool:
        text = self._build_text(metric, result)
        if self.dry_run:
            logger.info("Slack dry run: %s", text)
            return True
        if not self.webhook_url:
            logger.warning("SLACK_WEBHOOK_URL is not configured; alert was not sent")
            return False

        payload: dict[str, Any] = {
            "text": text,
            "blocks": self._build_blocks(metric, result),
        }
        if self.channel:
            payload["channel"] = self.channel

        try:
            response = self.session.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.error("Slack alert failed: %s", exc)
            return False

        return True

    def send_incident(self, incident: dict[str, Any]) -> bool:
        text = self._build_incident_text(incident)
        if self.dry_run:
            logger.info("Slack incident dry run: %s", text)
            return True
        if not self.webhook_url:
            logger.warning("SLACK_WEBHOOK_URL is not configured; incident was not sent")
            return False

        payload: dict[str, Any] = {
            "text": text,
            "blocks": self._build_incident_blocks(incident),
        }
        if self.channel:
            payload["channel"] = self.channel

        try:
            response = self.session.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.error("Slack incident alert failed: %s", exc)
            return False
        return True

    def _build_incident_text(self, incident: dict[str, Any]) -> str:
        severity = str(incident.get("severity", "warning")).upper()
        alerts = incident.get("alerts") or []
        titles = ", ".join(
            str(alert.get("title") or alert.get("metric") or "unknown")
            for alert in alerts
        )
        omitted = int(incident.get("omitted_count") or 0)
        suffix = f" (+{omitted} more)" if omitted else ""
        return (
            f"[INCIDENT][{severity}] {len(alerts)} related alerts: {titles}{suffix}. "
            "AI root cause analysis is running."
        )[:3000]

    def _build_incident_blocks(self, incident: dict[str, Any]) -> list[dict[str, Any]]:
        severity = str(incident.get("severity", "warning")).upper()
        alerts = incident.get("alerts") or []
        omitted = int(incident.get("omitted_count") or 0)
        title = f"[INCIDENT][{severity}] {len(alerts)} related alerts"
        if omitted:
            title += f" (+{omitted} more)"
        blocks: list[dict[str, Any]] = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": title[:150]},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Incident:* {incident.get('id', 'unknown')}"},
                    {"type": "mrkdwn", "text": f"*Severity:* {severity}"},
                    {"type": "mrkdwn", "text": f"*Started:* {incident.get('started_at', 'unknown')}"},
                    {"type": "mrkdwn", "text": f"*Detected:* {incident.get('detected_at', 'unknown')}"},
                    {
                        "type": "mrkdwn",
                        "text": f"*Metrics:* {incident.get('metric_count', len(alerts))}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Window:* {incident.get('window_seconds', 'unknown')}s",
                    },
                ],
            },
        ]

        lines: list[str] = []
        for alert in alerts:
            unit = str(alert.get("unit", ""))
            value = self._number_text(alert.get("value"), unit)
            reasons = "; ".join(alert.get("reasons") or [])
            reason_text = f" — {reasons}" if reasons else ""
            lines.append(
                f"- *{alert.get('title') or alert.get('metric')}* "
                f"[{str(alert.get('status', 'unknown')).upper()}] {value}{reason_text}"
            )
        if lines:
            blocks.append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "\n".join(lines)[:2900]},
                }
            )

        context = ["AI root cause analysis is running; the RCA will follow."]
        if self.grafana_root_url:
            context.append(
                f"<{self.grafana_root_url}/d/mern-overview|Open MERN Overview dashboard>"
            )
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": item[:300]} for item in context
                ],
            }
        )
        return blocks

    def _build_text(self, metric: MetricConfig, result: dict[str, Any]) -> str:
        severity = str(result.get("status", "unknown")).upper()
        value = self._value_text(metric, result.get("value"))
        reasons = "; ".join(result.get("reasons") or [])
        suffix = f" ({reasons})" if reasons else ""
        return f"[{severity}] {metric.title}: {value}{suffix}"

    def _build_blocks(self, metric: MetricConfig, result: dict[str, Any]) -> list[dict[str, Any]]:
        features = result.get("features") or {}
        severity = str(result.get("status", "unknown")).upper()
        reasons = result.get("reasons") or []
        blocks: list[dict[str, Any]] = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"[{severity}] {metric.title}"[:150],
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Value:* {self._value_text(metric, result.get('value'))}"},
                    {"type": "mrkdwn", "text": f"*Baseline mean:* {self._number_text(features.get('mean'), metric.unit)}"},
                    {"type": "mrkdwn", "text": f"*Std dev:* {self._number_text(features.get('std'), metric.unit)}"},
                    {"type": "mrkdwn", "text": f"*Z-score:* {self._number_text(features.get('z_score'))}"},
                    {"type": "mrkdwn", "text": f"*Robust z-score:* {self._number_text(features.get('robust_z_score'))}"},
                    {"type": "mrkdwn", "text": f"*Time:* {result.get('timestamp', 'unknown')}"},
                ],
            },
        ]

        if reasons:
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Why this fired:*\n" + "\n".join(f"- {reason}" for reason in reasons),
                    },
                }
            )

        if self.grafana_root_url:
            dashboard_url = f"{self.grafana_root_url}/d/mern-overview"
            blocks.append(
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": f"<{dashboard_url}|Open MERN Overview dashboard>"}
                    ],
                }
            )

        return blocks

    def _value_text(self, metric: MetricConfig, value: Any) -> str:
        return self._number_text(value, metric.unit)

    def _number_text(self, value: Any, unit: str = "") -> str:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return "n/a"
        suffix = f" {unit}" if unit else ""
        return f"{numeric:.4g}{suffix}"
