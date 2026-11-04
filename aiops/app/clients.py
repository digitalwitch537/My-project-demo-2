from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import requests


@dataclass(frozen=True)
class Sample:
    value: float
    labels: dict[str, str]


class MetricClientError(RuntimeError):
    pass


class _MetricClient:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": "mern-aiops/1.0"})

    def _query(self, path: str, expr: str, at: float | str | None) -> dict[str, Any]:
        params: dict[str, Any] = {"query": expr}
        if at is not None:
            params["time"] = at

        try:
            response = self.session.get(
                f"{self.base_url}{path}",
                params=params,
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise MetricClientError(f"request failed: {exc}") from exc

        if response.status_code >= 400:
            raise MetricClientError(
                f"query returned HTTP {response.status_code}: {response.text[:300]}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise MetricClientError("query returned invalid JSON") from exc

        if payload.get("status") != "success":
            raise MetricClientError(f"query failed: {payload.get('error', 'unknown error')}")

        return payload

    def _parse(self, payload: dict[str, Any]) -> Sample | None:
        data = payload.get("data") or {}
        result_type = data.get("resultType")
        result = data.get("result")

        if result_type == "vector":
            if not result:
                return None
            first = result[0]
            value = first.get("value") or [None, None]
            labels = first.get("metric") or {}
        elif result_type == "scalar":
            value = result or [None, None]
            labels = {}
        else:
            raise MetricClientError(f"unsupported result type: {result_type}")

        if len(value) < 2 or value[1] is None:
            return None

        try:
            numeric_value = float(value[1])
        except (TypeError, ValueError) as exc:
            raise MetricClientError(f"non-numeric query result: {value[1]!r}") from exc

        return Sample(value=numeric_value, labels={str(k): str(v) for k, v in labels.items()})


class PrometheusClient(_MetricClient):
    def query(self, expr: str, at: float | None = None) -> Sample | None:
        return self._parse(self._query("/api/v1/query", expr, at))


class LokiClient(_MetricClient):
    def query(self, expr: str, at: float | None = None) -> Sample | None:
        time_value = (
            datetime.fromtimestamp(at, tz=timezone.utc).isoformat() if at is not None else None
        )
        return self._parse(self._query("/loki/api/v1/query", expr, time_value))
