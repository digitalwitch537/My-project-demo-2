from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from .collector import (
    LokiRangeClient,
    PrometheusRangeClient,
    collect_logs,
    collect_metric_evidence,
)
from .config import AppConfig
from .ollama_client import OllamaClient
from .prompt import build_prompt, build_repair_prompt

logger = logging.getLogger(__name__)


class Analysis(BaseModel):
    summary: str
    root_cause: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    remediation: list[str] = Field(default_factory=list)
    needs_human: bool = True
    missing_data: list[str] = Field(default_factory=list)


class AnalysisParseError(ValueError):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, str):
        normalized = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return _now()
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    return _now()


def _extract_json(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        lines = [line for line in text.splitlines() if not line.strip().startswith("```")]
        text = "\n".join(lines).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise AnalysisParseError("response did not contain a JSON object")

    try:
        payload = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise AnalysisParseError(f"invalid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise AnalysisParseError("JSON response is not an object")
    return payload


def _to_text(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("step", "action", "description", "detail", "text"):
            if value.get(key):
                return str(value[key])
        return json.dumps(value, sort_keys=True)
    return str(value)


def _to_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (str, dict)):
        return [_to_text(value)]
    if isinstance(value, (list, tuple)):
        return [_to_text(item) for item in value if str(item).strip()]
    return [str(value)]


def _to_float(value: Any) -> float:
    if isinstance(value, str) and value.strip().lower() in {"high", "medium", "low"}:
        return {"high": 0.9, "medium": 0.6, "low": 0.3}[value.strip().lower()]
    return float(value)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return True
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def parse_analysis(content: str) -> Analysis:
    payload = _extract_json(content)
    try:
        normalized = {
            "summary": str(payload.get("summary", "")).strip(),
            "root_cause": str(payload.get("root_cause", "")).strip(),
            "confidence": _to_float(payload.get("confidence", 0.0)),
            "evidence": _to_list(payload.get("evidence")),
            "remediation": _to_list(payload.get("remediation")),
            "needs_human": _to_bool(payload.get("needs_human", True)),
            "missing_data": _to_list(payload.get("missing_data")),
        }
        if not normalized["summary"]:
            raise AnalysisParseError("response is missing a summary")
        if not normalized["root_cause"]:
            raise AnalysisParseError("response is missing a root_cause")
        return Analysis.model_validate(normalized)
    except (ValidationError, TypeError, ValueError) as exc:
        raise AnalysisParseError(f"response does not match schema: {exc}") from exc


def _trim_metric_evidence(
    metric_evidence: list[dict[str, Any]],
    max_points: int = 8,
) -> list[dict[str, Any]]:
    trimmed: list[dict[str, Any]] = []
    for item in metric_evidence:
        reduced = dict(item)
        points = reduced.get("points")
        if isinstance(points, list):
            reduced["points"] = points[-max(1, max_points):]
        trimmed.append(reduced)
    return trimmed


def _fallback_analysis(
    reason: str,
    metric_evidence: list[dict[str, Any]],
    logs: list[dict[str, Any]],
) -> Analysis:
    evidence = [
        f"Collected {len(metric_evidence)} metric summaries and {len(logs)} log lines."
    ]
    if reason:
        evidence.append(reason)
    return Analysis(
        summary="AI RCA did not produce a validated analysis.",
        root_cause="No model-validated root cause was produced; see model_error and evidence.",
        confidence=0.0,
        evidence=evidence,
        remediation=[
            "Check mern-ai-model and Ollama container logs.",
            "Review the collected metrics and logs manually.",
        ],
        needs_human=True,
        missing_data=[reason] if reason else [],
    )


class Analyzer:
    def __init__(
        self,
        config: AppConfig,
        prometheus: PrometheusRangeClient | None = None,
        loki: LokiRangeClient | None = None,
        ollama: OllamaClient | None = None,
    ) -> None:
        self.config = config
        self.prometheus = prometheus or PrometheusRangeClient(
            config.prometheus_url,
            config.collection.request_timeout_seconds,
        )
        self.loki = loki or LokiRangeClient(
            config.loki_url,
            config.collection.request_timeout_seconds,
        )
        self.ollama = ollama or OllamaClient(
            base_url=config.ollama.url,
            model=config.ollama.model,
            timeout_seconds=config.ollama.timeout_seconds,
            num_ctx=config.ollama.num_ctx,
            num_predict=config.ollama.num_predict,
            temperature=config.ollama.temperature,
            keep_alive=config.ollama.keep_alive,
        )

    def analyze(self, job: dict[str, Any]) -> dict[str, Any]:
        payload = job.get("payload") or {}
        triggered_at = _parse_timestamp(payload.get("triggered_at"))
        window_seconds = int(
            payload.get("window_seconds") or self.config.collection.window_seconds
        )
        end = triggered_at.timestamp()
        start = end - max(window_seconds, 1)

        metric_definitions = payload.get("related_metrics") or [
            payload.get("metric") or {}
        ]
        metric_evidence, metric_errors = collect_metric_evidence(
            self.prometheus,
            self.loki,
            [definition for definition in metric_definitions if definition],
            start,
            end,
            self.config.collection.step_seconds,
            self.config.collection.max_metric_points,
        )
        logs, log_errors = collect_logs(
            self.loki,
            self.config.collection.log_queries,
            start,
            end,
            self.config.collection.max_log_lines,
            self.config.collection.max_log_chars,
            self.config.collection.max_log_line_chars,
        )
        collection_errors = metric_errors + log_errors

        analysis: Analysis | None = None
        model_error: str | None = None
        raw_response: str | None = None

        if not metric_evidence and not logs:
            model_error = "no metrics or logs available"
        else:
            system_prompt, user_prompt = build_prompt(
                payload,
                metric_evidence,
                logs,
                collection_errors,
                window_seconds,
            )
            try:
                raw_response = self.ollama.chat(system_prompt, user_prompt)
                analysis = parse_analysis(raw_response)
            except Exception as exc:
                model_error = str(exc)
                if raw_response:
                    try:
                        repair_prompt = build_repair_prompt(
                            raw_response, window_seconds
                        )
                        repaired = self.ollama.chat(system_prompt, repair_prompt)
                        analysis = parse_analysis(repaired)
                        raw_response = repaired
                        model_error = None
                    except Exception as repair_exc:
                        model_error = f"{model_error}; repair failed: {repair_exc}"
                else:
                    try:
                        reduced_system, reduced_prompt = build_prompt(
                            payload,
                            _trim_metric_evidence(metric_evidence),
                            logs[-200:],
                            collection_errors,
                            window_seconds,
                        )
                        raw_response = self.ollama.chat(
                            reduced_system, reduced_prompt
                        )
                        analysis = parse_analysis(raw_response)
                        model_error = None
                    except Exception as retry_exc:
                        model_error = (
                            f"{model_error}; reduced-evidence retry failed: "
                            f"{retry_exc}"
                        )

        if analysis is None:
            analysis = _fallback_analysis(
                model_error or "analysis unavailable",
                metric_evidence,
                logs,
            )

        result = {
            "job_id": job.get("job_id"),
            "event_id": payload.get("event_id"),
            "triggered_at": payload.get("triggered_at"),
            "analyzed_at": _now().isoformat(),
            "window_seconds": window_seconds,
            "model": self.config.ollama.model,
            "status": "analyzed" if model_error is None else "fallback",
            "analysis": analysis.model_dump(),
            "metric_evidence": metric_evidence,
            "logs": logs,
            "log_count": len(logs),
            "collection_errors": collection_errors,
            "model_error": model_error,
        }
        if model_error:
            logger.warning("AI analysis fallback for %s: %s", payload.get("event_id"), model_error)
        return result
