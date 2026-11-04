from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from typing import Any

import requests

_IMPORTANT_LOG_RE = re.compile(
    r"(?i)\b(error|exception|fail(?:ed|ure)?|fatal|panic|timeout|timed out|"
    r"refused|unavailable|unhealthy|oom|killed|crash(?:ed)?|5\d\d)\b"
)


class RangeClientError(RuntimeError):
    pass


class _BaseRangeClient:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": "mern-ai-model/1.0"})

    def _query(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self.session.get(
                f"{self.base_url}{path}",
                params=params,
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise RangeClientError(f"request failed: {exc}") from exc

        if response.status_code >= 400:
            raise RangeClientError(
                f"query returned HTTP {response.status_code}: {response.text[:300]}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise RangeClientError("query returned invalid JSON") from exc

        if payload.get("status") != "success":
            raise RangeClientError(
                f"query failed: {payload.get('error', 'unknown error')}"
            )
        return payload


def _parse_matrix(result: Any) -> list[dict[str, Any]]:
    if not isinstance(result, list):
        raise RangeClientError("query result is not a list")

    series_list: list[dict[str, Any]] = []
    for item in result:
        if not isinstance(item, dict):
            continue
        values: list[tuple[float, float]] = []
        for point in item.get("values") or []:
            if not isinstance(point, (list, tuple)) or len(point) < 2:
                continue
            try:
                timestamp = float(point[0])
                value = float(point[1])
            except (TypeError, ValueError):
                continue
            if math.isfinite(value):
                values.append((timestamp, value))
        if values:
            series_list.append(
                {
                    "labels": {
                        str(key): str(value)
                        for key, value in (item.get("metric") or {}).items()
                    },
                    "values": values,
                }
            )
    return series_list


class PrometheusRangeClient(_BaseRangeClient):
    def query_range(
        self,
        expr: str,
        start: float,
        end: float,
        step_seconds: int,
    ) -> list[dict[str, Any]]:
        payload = self._query(
            "/api/v1/query_range",
            {
                "query": expr,
                "start": start,
                "end": end,
                "step": step_seconds,
            },
        )
        data = payload.get("data") or {}
        result_type = data.get("resultType")
        if result_type not in {"matrix", "vector"}:
            raise RangeClientError(f"unsupported result type: {result_type}")
        if result_type == "vector":
            return _parse_matrix(
                [
                    {
                        "metric": item.get("metric", {}),
                        "values": [item.get("value")]
                        if item.get("value") is not None
                        else [],
                    }
                    for item in data.get("result") or []
                    if isinstance(item, dict)
                ]
            )
        return _parse_matrix(data.get("result"))


class LokiRangeClient(_BaseRangeClient):
    def query_metric_range(
        self,
        expr: str,
        start: float,
        end: float,
        step_seconds: int,
    ) -> list[dict[str, Any]]:
        payload = self._query(
            "/loki/api/v1/query_range",
            {
                "query": expr,
                "start": int(start * 1_000_000_000),
                "end": int(end * 1_000_000_000),
                "step": f"{step_seconds}s",
            },
        )
        data = payload.get("data") or {}
        result_type = data.get("resultType")
        if result_type != "matrix":
            raise RangeClientError(
                f"expected a metric matrix, received: {result_type}"
            )
        return _parse_matrix(data.get("result"))

    def query_logs(
        self,
        expr: str,
        start: float,
        end: float,
        limit: int,
    ) -> list[dict[str, Any]]:
        payload = self._query(
            "/loki/api/v1/query_range",
            {
                "query": expr,
                "start": int(start * 1_000_000_000),
                "end": int(end * 1_000_000_000),
                "limit": limit,
                "direction": "backward",
            },
        )
        data = payload.get("data") or {}
        result_type = data.get("resultType")
        if result_type != "streams":
            raise RangeClientError(
                f"expected log streams, received: {result_type}"
            )

        entries: list[dict[str, Any]] = []
        for stream in data.get("result") or []:
            if not isinstance(stream, dict):
                continue
            labels = {
                str(key): str(value)
                for key, value in (stream.get("stream") or {}).items()
            }
            for item in stream.get("values") or []:
                if not isinstance(item, (list, tuple)) or len(item) < 2:
                    continue
                try:
                    timestamp_ns = int(item[0])
                except (TypeError, ValueError):
                    continue
                entries.append(
                    {
                        "timestamp_ns": timestamp_ns,
                        "timestamp": datetime.fromtimestamp(
                            timestamp_ns / 1_000_000_000,
                            tz=timezone.utc,
                        ).isoformat(),
                        "labels": labels,
                        "line": str(item[1]),
                    }
                )

        entries.sort(key=lambda entry: entry["timestamp_ns"])
        return entries


def summarize_series(series: dict[str, Any], max_points: int) -> dict[str, Any]:
    values = series.get("values") or []
    if not values:
        return {"labels": series.get("labels", {}), "samples": 0}

    numeric = [value for _, value in values]
    start_timestamp = values[0][0]
    end_timestamp = values[-1][0]
    stride = max(1, math.ceil(len(values) / max(max_points, 1)))
    selected = values[::stride]
    if selected[-1] != values[-1]:
        selected.append(values[-1])

    return {
        "labels": series.get("labels", {}),
        "samples": len(values),
        "first": numeric[0],
        "last": numeric[-1],
        "min": min(numeric),
        "max": max(numeric),
        "mean": sum(numeric) / len(numeric),
        "delta": numeric[-1] - numeric[0],
        "start": datetime.fromtimestamp(
            start_timestamp, tz=timezone.utc
        ).isoformat(),
        "end": datetime.fromtimestamp(end_timestamp, tz=timezone.utc).isoformat(),
        "points": [
            {
                "timestamp": datetime.fromtimestamp(
                    timestamp, tz=timezone.utc
                ).isoformat(),
                "value": value,
            }
            for timestamp, value in selected
        ],
    }


def collect_metric_evidence(
    prometheus: PrometheusRangeClient,
    loki: LokiRangeClient,
    metric_definitions: list[dict[str, Any]],
    start: float,
    end: float,
    step_seconds: int,
    max_points: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    evidence: list[dict[str, Any]] = []
    errors: list[str] = []

    for definition in metric_definitions:
        if not isinstance(definition, dict):
            continue
        metric_id = str(definition.get("id", "unknown"))
        title = str(definition.get("title", metric_id))
        source = str(definition.get("source", "prometheus")).lower()
        query = str(definition.get("query", "")).strip()
        unit = str(definition.get("unit", ""))
        if not query:
            errors.append(f"{metric_id}: empty query")
            continue

        try:
            if source == "prometheus":
                series_list = prometheus.query_range(
                    query, start, end, step_seconds
                )
            elif source == "loki":
                series_list = loki.query_metric_range(
                    query, start, end, step_seconds
                )
            else:
                raise RangeClientError(f"unsupported metric source: {source}")

            if not series_list:
                evidence.append(
                    {
                        "id": metric_id,
                        "title": title,
                        "source": source,
                        "unit": unit,
                        "samples": 0,
                        "note": "no series returned",
                    }
                )
                continue

            for series in series_list:
                summary = summarize_series(series, max_points)
                summary.update(
                    {
                        "id": metric_id,
                        "title": title,
                        "source": source,
                        "unit": unit,
                    }
                )
                evidence.append(summary)
        except Exception as exc:
            errors.append(f"{metric_id}: {exc}")

    return evidence, errors


def _log_source(labels: dict[str, Any]) -> str:
    for key in ("container", "service", "job"):
        value = labels.get(key)
        if value:
            return str(value)
    return "unknown"


def _sanitize_log_line(line: str, max_chars: int) -> str:
    clean = line.replace("\x00", "").replace("\r", "").strip()
    if len(clean) > max_chars:
        return clean[:max_chars] + "..."
    return clean


def collect_logs(
    loki: LokiRangeClient,
    queries: tuple[str, ...],
    start: float,
    end: float,
    max_lines: int,
    max_chars: int,
    max_line_chars: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    entries: list[dict[str, Any]] = []
    errors: list[str] = []
    seen: set[tuple[int, str]] = set()

    for query in queries:
        try:
            batch = loki.query_logs(query, start, end, max_lines)
        except Exception as exc:
            errors.append(f"logs {query}: {exc}")
            continue

        for entry in batch:
            key = (entry["timestamp_ns"], entry["line"])
            if key in seen:
                continue
            seen.add(key)
            line = _sanitize_log_line(entry["line"], max_line_chars)
            if not line:
                continue
            entries.append(
                {
                    "timestamp": entry["timestamp"],
                    "timestamp_ns": entry["timestamp_ns"],
                    "source": _log_source(entry["labels"]),
                    "line": line,
                    "important": bool(_IMPORTANT_LOG_RE.search(line)),
                }
            )

    important = sorted(
        (entry for entry in entries if entry["important"]),
        key=lambda entry: entry["timestamp_ns"],
        reverse=True,
    )
    other = sorted(
        (entry for entry in entries if not entry["important"]),
        key=lambda entry: entry["timestamp_ns"],
        reverse=True,
    )

    selected: list[dict[str, Any]] = []
    used_chars = 0
    for entry in important + other:
        if len(selected) >= max_lines:
            break
        cost = len(entry["line"]) + len(entry["source"]) + 64
        if used_chars + cost > max_chars:
            continue
        selected.append(entry)
        used_chars += cost

    selected.sort(key=lambda entry: entry["timestamp_ns"])
    return selected, errors
