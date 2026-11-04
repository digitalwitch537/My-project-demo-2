from pathlib import Path

from app.config import load_config


def test_ai_model_settings_can_be_overridden(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AIOPS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AI_MODEL_ENABLED", "false")
    monkeypatch.setenv("AI_MODEL_URL", "http://ai-model.local:8090/")
    monkeypatch.setenv("AI_MODEL_TIMEOUT_SECONDS", "2.5")
    monkeypatch.setenv("AI_MODEL_WINDOW_SECONDS", "600")

    config = load_config(Path(__file__).parents[1] / "config.yml")

    assert config.ai_model.enabled is False
    assert config.ai_model.url == "http://ai-model.local:8090"
    assert config.ai_model.timeout_seconds == 2.5
    assert config.ai_model.window_seconds == 600
