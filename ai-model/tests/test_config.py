from pathlib import Path

from app.config import load_config


def test_environment_overrides_config(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AI_MODEL_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AI_MODEL_HOST", "127.0.0.1")
    monkeypatch.setenv("AI_MODEL_PORT", "9090")
    monkeypatch.setenv("AI_MODEL_WINDOW_SECONDS", "600")
    monkeypatch.setenv("AI_MODEL_COLLECTION_TIMEOUT_SECONDS", "7.5")
    monkeypatch.setenv("OLLAMA_MODEL", "test-model")
    monkeypatch.setenv("SLACK_ENABLED", "false")
    monkeypatch.setenv("SLACK_DRY_RUN", "true")

    config = load_config(Path(__file__).parents[1] / "config.yml")

    assert config.host == "127.0.0.1"
    assert config.port == 9090
    assert config.collection.window_seconds == 600
    assert config.collection.request_timeout_seconds == 7.5
    assert config.ollama.model == "test-model"
    assert config.slack.enabled is False
    assert config.slack.dry_run is True
    assert config.data_dir == tmp_path
