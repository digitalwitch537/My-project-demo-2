import json

import pytest

from app.analyzer import Analyzer, AnalysisParseError, parse_analysis
from app.ollama_client import OllamaError


class FakePrometheus:
    def query_range(self, query: str, start: float, end: float, step: int):
        return [
            {
                "labels": {"job": "mern-backend"},
                "values": [(start, 1.0), (end, 12.0)],
            }
        ]


class FakeLoki:
    def query_metric_range(self, query: str, start: float, end: float, step: int):
        return [
            {
                "labels": {"container": "mern-frontend"},
                "values": [(start, 2.0), (end, 3.0)],
            }
        ]

    def query_logs(self, query: str, start: float, end: float, limit: int):
        return [
            {
                "timestamp_ns": 1700000000000000000,
                "timestamp": "2023-11-14T22:13:20+00:00",
                "labels": {"container": "mern-backend"},
                "line": "ERROR database connection timeout",
            }
        ]


class FakeOllama:
    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, str]] = []

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        self.calls.append((system_prompt, user_prompt))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def valid_analysis() -> str:
    return json.dumps(
        {
            "summary": "Database connection pool exhausted",
            "root_cause": "Backend exhausted MongoDB connections",
            "confidence": 0.82,
            "evidence": ["5xx rate rose with connection timeouts"],
            "remediation": ["Increase the MongoDB connection pool", "Restart the backend"],
            "needs_human": True,
            "missing_data": ["MongoDB connection metrics"],
        }
    )


def test_analyzer_collects_evidence_and_calls_ollama(config, alert_payload) -> None:
    ollama = FakeOllama([valid_analysis()])
    analyzer = Analyzer(
        config,
        prometheus=FakePrometheus(),
        loki=FakeLoki(),
        ollama=ollama,
    )

    result = analyzer.analyze({"job_id": "job-1", "payload": alert_payload})

    assert result["status"] == "analyzed"
    assert result["analysis"]["confidence"] == pytest.approx(0.82)
    assert result["log_count"] == 1
    assert result["metric_evidence"][0]["labels"]["job"] == "mern-backend"
    assert not result["collection_errors"]
    assert len(ollama.calls) == 1


def test_analyzer_falls_back_when_ollama_is_unavailable(config, alert_payload) -> None:
    analyzer = Analyzer(
        config,
        prometheus=FakePrometheus(),
        loki=FakeLoki(),
        ollama=FakeOllama([OllamaError("connection refused")]),
    )

    result = analyzer.analyze({"job_id": "job-2", "payload": alert_payload})

    assert result["status"] == "fallback"
    assert result["analysis"]["needs_human"] is True
    assert "connection refused" in result["model_error"]


def test_analyzer_repairs_invalid_json(config, alert_payload) -> None:
    ollama = FakeOllama(["not json", valid_analysis()])
    analyzer = Analyzer(
        config,
        prometheus=FakePrometheus(),
        loki=FakeLoki(),
        ollama=ollama,
    )

    result = analyzer.analyze({"job_id": "job-3", "payload": alert_payload})

    assert result["status"] == "analyzed"
    assert result["analysis"]["confidence"] == pytest.approx(0.82)
    assert len(ollama.calls) == 2


def test_parse_analysis_rejects_invalid_confidence() -> None:
    with pytest.raises(AnalysisParseError):
        parse_analysis(
            json.dumps(
                {
                    "summary": "test",
                    "root_cause": "test",
                    "confidence": 2.0,
                }
            )
        )
