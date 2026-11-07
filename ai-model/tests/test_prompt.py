from app.prompt import build_prompt


def test_prompt_contains_evidence_and_injection_warning(alert_payload: dict) -> None:
    logs = [
        {
            "timestamp": "2026-01-01T00:05:00+00:00",
            "source": "mern-backend",
            "line": "ERROR connection refused",
        }
    ]

    system_prompt, user_prompt = build_prompt(
        alert_payload,
        [{"id": "api_5xx_rate", "last": 12.0}],
        logs,
        ["logs: timeout"],
        900,
    )

    assert "untrusted data" in system_prompt
    assert "connection refused" in user_prompt
    assert "collection_errors" in user_prompt
    assert "analysis_window_seconds" in user_prompt
    assert "log_clusters" in user_prompt
    assert "incident_timeline" in user_prompt
