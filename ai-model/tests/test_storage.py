from pathlib import Path

from app.storage import JobStore


def test_job_store_enqueue_dedupe_and_complete(tmp_path: Path) -> None:
    store = JobStore(tmp_path)
    payload = {"event_id": "event-1", "metric": {"id": "cpu"}}

    job_id, created = store.enqueue(payload)
    duplicate_id, duplicate_created = store.enqueue(payload)

    assert created is True
    assert duplicate_created is False
    assert duplicate_id == job_id
    assert store.pending_count() == 1

    job = store.next_pending()
    assert job is not None
    assert job["event_id"] == "event-1"

    store.complete(job_id, {"analysis": {"root_cause": "test"}})

    stored = store.get(job_id)
    assert stored is not None
    assert stored["status"] == "done"
    assert stored["result"]["analysis"]["root_cause"] == "test"
    assert store.pending_count() == 0


def test_job_store_marks_failed(tmp_path: Path) -> None:
    store = JobStore(tmp_path)
    job_id, _ = store.enqueue({"event_id": "event-2"})

    store.fail(job_id, "ollama unavailable")

    stored = store.get(job_id)
    assert stored is not None
    assert stored["status"] == "failed"
    assert stored["error"] == "ollama unavailable"
