import json

from app.queue import AnalysisWorker
from app.storage import JobStore


class FakeAnalyzer:
    def analyze(self, job: dict) -> dict:
        return {
            "job_id": job["job_id"],
            "event_id": job["payload"]["event_id"],
            "status": "analyzed",
            "analysis": {"root_cause": "test"},
        }


class FailingAnalyzer:
    def analyze(self, job: dict) -> dict:
        raise RuntimeError("model unavailable")


class FakeNotifier:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def send_analysis(self, job: dict, result: dict) -> bool:
        self.calls.append({"job": job, "result": result})
        return True


def test_worker_processes_pending_job(config, alert_payload) -> None:
    store = JobStore(config.data_dir)
    notifier = FakeNotifier()
    job_id, created = store.enqueue(alert_payload)
    worker = AnalysisWorker(config, store, FakeAnalyzer(), notifier)

    assert created is True
    assert worker.run_once() is True
    assert worker.run_once() is False

    stored = store.get(job_id)
    assert stored is not None
    assert stored["status"] == "done"
    assert stored["result"]["notification_sent"] is True
    assert notifier.calls[0]["job"]["job_id"] == job_id

    analyses = (config.data_dir / "analyses.jsonl").read_text(encoding="utf-8")
    assert json.loads(analyses.splitlines()[0])["event_id"] == alert_payload["event_id"]


def test_worker_records_failure(config, alert_payload) -> None:
    store = JobStore(config.data_dir)
    job_id, _ = store.enqueue(alert_payload)
    worker = AnalysisWorker(config, store, FailingAnalyzer(), FakeNotifier())

    assert worker.run_once() is True

    stored = store.get(job_id)
    assert stored is not None
    assert stored["status"] == "failed"
    assert "model unavailable" in stored["error"]

    failures = (config.data_dir / "failures.jsonl").read_text(encoding="utf-8")
    assert json.loads(failures.splitlines()[0])["job_id"] == job_id
