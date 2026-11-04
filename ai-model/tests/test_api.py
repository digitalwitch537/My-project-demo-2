from fastapi.testclient import TestClient

from app.api import create_app
from app.storage import JobStore


def test_api_queues_alert_and_returns_job(config, alert_payload) -> None:
    store = JobStore(config.data_dir)
    app = create_app(config, store, worker=None)
    client = TestClient(app)

    response = client.post("/analyze", json=alert_payload)
    duplicate = client.post("/analyze", json=alert_payload)

    assert response.status_code == 202
    assert response.json()["status"] == "queued"
    assert duplicate.status_code == 202
    assert duplicate.json()["status"] == "duplicate"

    job_id = response.json()["job_id"]
    job_response = client.get(f"/jobs/{job_id}")
    assert job_response.status_code == 200
    assert job_response.json()["status"] == "pending"
    assert job_response.json()["payload"]["event_id"] == alert_payload["event_id"]

    health = client.get("/healthz")
    assert health.status_code == 200
    assert health.json()["pending_jobs"] == 1
    assert health.json()["model"] == config.ollama.model


def test_api_rejects_invalid_window_and_missing_job(config, alert_payload) -> None:
    app = create_app(config, JobStore(config.data_dir), worker=None)
    client = TestClient(app)
    invalid = dict(alert_payload)
    invalid["window_seconds"] = 10

    assert client.post("/analyze", json=invalid).status_code == 422
    assert client.get("/jobs/does-not-exist").status_code == 404
