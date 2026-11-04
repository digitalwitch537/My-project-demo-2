from app.notifier import SlackNotifier


class FakeResponse:
    status_code = 200
    text = ""

    def raise_for_status(self) -> None:
        return None


class FakeSession:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def post(self, url: str, json: dict, timeout: float) -> FakeResponse:
        self.calls.append({"url": url, "json": json, "timeout": timeout})
        return FakeResponse()


def analysis_result() -> dict:
    return {
        "event_id": "event-1",
        "status": "analyzed",
        "model": "gemma3:4b",
        "window_seconds": 360,
        "log_count": 2,
        "analysis": {
            "summary": "Database pool exhausted",
            "root_cause": "The backend exhausted MongoDB connections",
            "confidence": 0.8,
            "evidence": ["connection timeout"],
            "remediation": ["Increase the pool size"],
            "needs_human": True,
            "missing_data": [],
        },
    }


def alert_job() -> dict:
    return {
        "payload": {
            "metric": {"id": "api_5xx_rate", "title": "API 5xx rate"},
            "result": {"status": "critical"},
        }
    }


def test_notifier_sends_structured_slack_message() -> None:
    session = FakeSession()
    notifier = SlackNotifier(
        webhook_url="https://hooks.slack.test/abc",
        enabled=True,
        dry_run=False,
        timeout_seconds=1.0,
        channel="#alerts",
        grafana_root_url="http://grafana:3000",
        session=session,
    )

    assert notifier.send_analysis(alert_job(), analysis_result()) is True
    payload = session.calls[0]["json"]

    assert payload["channel"] == "#alerts"
    assert "AI RCA" in payload["text"]
    assert "exhausted MongoDB connections" in payload["text"]
    assert any(
        "MongoDB" in block.get("text", {}).get("text", "")
        for block in payload["blocks"]
    )
    assert any(
        "mern-overview" in element.get("text", "")
        for block in payload["blocks"]
        for element in block.get("elements", [])
    )


def test_notifier_marks_fallback_analysis() -> None:
    session = FakeSession()
    result = analysis_result()
    result["status"] = "fallback"
    notifier = SlackNotifier(
        webhook_url="https://hooks.slack.test/abc",
        enabled=True,
        dry_run=False,
        timeout_seconds=1.0,
        channel="",
        grafana_root_url="",
        session=session,
    )

    assert notifier.send_analysis(alert_job(), result) is True
    assert "AI RCA UNAVAILABLE" in session.calls[0]["json"]["text"]


def test_notifier_uses_dashboard_url_from_alert_payload() -> None:
    session = FakeSession()
    job = alert_job()
    job["payload"]["grafana_root_url"] = "http://alert-grafana:3000/"
    notifier = SlackNotifier(
        webhook_url="https://hooks.slack.test/abc",
        enabled=True,
        dry_run=False,
        timeout_seconds=1.0,
        channel="",
        grafana_root_url="",
        session=session,
    )

    assert notifier.send_analysis(job, analysis_result()) is True
    assert any(
        "http://alert-grafana:3000/d/mern-overview" in element.get("text", "")
        for block in session.calls[0]["json"]["blocks"]
        for element in block.get("elements", [])
    )


def test_notifier_skips_without_webhook() -> None:
    notifier = SlackNotifier(
        webhook_url="",
        enabled=True,
        dry_run=False,
        timeout_seconds=1.0,
        channel="",
        grafana_root_url="",
        session=FakeSession(),
    )

    assert notifier.send_analysis(alert_job(), analysis_result()) is False
