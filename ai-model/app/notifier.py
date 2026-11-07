from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


def _truncate(value: Any, limit: int) -> str:
    text = str(value)
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


class SlackNotifier:
    def __init__(
        self,
        webhook_url: str,
        enabled: bool,
        dry_run: bool,
        timeout_seconds: float,
        channel: str,
        grafana_root_url: str,
        session: requests.Session | None = None,
    ) -> None:
        self.webhook_url = webhook_url
        self.enabled = enabled
        self.dry_run = dry_run
        self.timeout_seconds = timeout_seconds
        self.channel = channel
        self.grafana_root_url = grafana_root_url.rstrip("/")
        self.session = session or requests.Session()

    def send_analysis(self, job: dict[str, Any], result: dict[str, Any]) -> bool:
        payload = job.get("payload") or {}
        metric = payload.get("metric") or {}
        incident = payload.get("incident") or {}
        analysis = result.get("analysis") or {}
        title = self._analysis_title(metric, incident)
        fallback = result.get("status") != "analyzed"
        if fallback:
            logger.warning(
                "Skipped generic Slack RCA for %s because the analysis failed",
                payload.get("event_id"),
            )
            return False
        text = f"[AI RCA] {title}: {analysis.get('root_cause') or 'unknown'}"
        if not self.enabled:
            logger.info("Slack notifications are disabled")
            return False
        if self.dry_run:
            logger.info("Slack dry run: %s", text)
            return True
        if not self.webhook_url:
            logger.warning("SLACK_WEBHOOK_URL is not configured; RCA was not sent")
            return False

        body: dict[str, Any] = {
            "text": _truncate(text, 3000),
            "blocks": self._build_blocks(job, result),
        }
        if self.channel:
            body["channel"] = self.channel

        try:
            response = self.session.post(
                self.webhook_url,
                json=body,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.error("Slack RCA failed: %s", exc)
            return False
        return True

    def _analysis_title(
        self,
        metric: dict[str, Any],
        incident: dict[str, Any],
    ) -> str:
        if incident:
            count = incident.get("metric_count") or len(incident.get("alerts") or [])
            return f"Correlated incident ({count} metrics)"
        return str(metric.get("title") or metric.get("id") or "Unknown metric")

    def _build_blocks(
        self,
        job: dict[str, Any],
        result: dict[str, Any],
    ) -> list[dict[str, Any]]:
        payload = job.get("payload") or {}
        metric = payload.get("metric") or {}
        incident = payload.get("incident") or {}
        analysis = result.get("analysis") or {}
        title = self._analysis_title(metric, incident)
        confidence = float(analysis.get("confidence") or 0.0)
        grafana_root_url = (
            self.grafana_root_url
            or str(payload.get("grafana_root_url") or "").rstrip("/")
        )

        fields = [
            {
                "type": "mrkdwn",
                "text": f"*Status:* {_truncate(payload.get('result', {}).get('status', 'unknown'), 80)}",
            },
            {
                "type": "mrkdwn",
                "text": f"*Confidence:* {confidence:.0%}",
            },
            {
                "type": "mrkdwn",
                "text": f"*Model:* {_truncate(result.get('model', 'unknown'), 80)}",
            },
            {
                "type": "mrkdwn",
                "text": f"*Window:* {result.get('window_seconds', 'unknown')}s",
            },
        ]
        if incident:
            fields.extend(
                [
                    {
                        "type": "mrkdwn",
                        "text": f"*Incident:* {_truncate(incident.get('id', 'unknown'), 80)}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Metrics:* {incident.get('metric_count', 'unknown')}",
                    },
                ]
            )

        blocks: list[dict[str, Any]] = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": _truncate(f"[AI RCA] {title}", 150),
                },
            },
            {
                "type": "section",
                "fields": fields,
            },
        ]

        summary = str(analysis.get("summary") or "").strip()
        if summary:
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": _truncate(f"*Summary*\n{summary}", 2900),
                    },
                }
            )

        root_cause = str(analysis.get("root_cause") or "Not determined").strip()
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": _truncate(f"*Root cause*\n{root_cause}", 2900),
                },
            }
        )

        evidence = analysis.get("evidence") or []
        if evidence:
            bullets = "\n".join(
                f"- {_truncate(item, 300)}" for item in evidence[:8]
            )
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": _truncate(f"*Evidence*\n{bullets}", 2900),
                    },
                }
            )

        remediation = analysis.get("remediation") or []
        if remediation:
            steps = "\n".join(
                f"{index}. {_truncate(item, 300)}"
                for index, item in enumerate(remediation[:8], start=1)
            )
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": _truncate(f"*Remediation*\n{steps}", 2900),
                    },
                }
            )

        missing_data = analysis.get("missing_data") or []
        if missing_data:
            missing = "\n".join(
                f"- {_truncate(item, 300)}" for item in missing_data[:6]
            )
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": _truncate(f"*Missing data*\n{missing}", 2900),
                    },
                }
            )

        context = [
            f"Event: {_truncate(result.get('event_id', 'unknown'), 80)}",
            f"Logs collected: {result.get('log_count', 0)}",
        ]
        if incident:
            context.append(
                f"Incident: {_truncate(incident.get('id', 'unknown'), 80)}"
            )
        if result.get("model_error"):
            context.append(f"Analysis error: {_truncate(result['model_error'], 300)}")
        if grafana_root_url:
            context.append(
                f"<{grafana_root_url}/d/mern-overview|Open MERN Overview dashboard>"
            )
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": _truncate(item, 300)}
                    for item in context
                ],
            }
        )
        return blocks
