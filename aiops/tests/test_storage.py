import json
from pathlib import Path

from app.storage import JsonlWriter, StateStore, write_json_atomic


def test_state_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    store = StateStore(path)
    state = {"version": 1, "metrics": {"cpu": {"history": [{"value": 12.5}]}}}

    store.save(state)

    assert store.load() == state


def test_corrupt_state_is_quarantined(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    path.write_text("{not-json", encoding="utf-8")
    store = StateStore(path)

    loaded = store.load()

    assert loaded == {"version": 1, "metrics": {}}
    assert not path.exists()
    assert list(tmp_path.glob("state.corrupt.*.json"))


def test_jsonl_writer_rotates(tmp_path: Path) -> None:
    path = tmp_path / "results.jsonl"
    writer = JsonlWriter(path, max_bytes=1)

    writer.append({"value": 1})
    writer.append({"value": 2})

    backup = path.with_suffix(".jsonl.1")
    assert path.exists()
    assert backup.exists()
    assert json.loads(path.read_text(encoding="utf-8").strip()) == {"value": 2}
    assert json.loads(backup.read_text(encoding="utf-8").strip()) == {"value": 1}


def test_write_json_atomic(tmp_path: Path) -> None:
    path = tmp_path / "latest.json"

    write_json_atomic(path, {"status": "ok"})

    assert json.loads(path.read_text(encoding="utf-8")) == {"status": "ok"}
