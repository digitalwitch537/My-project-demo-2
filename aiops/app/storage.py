from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


def write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f"{path.name}.tmp")
    temporary_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary_path, path)


class StateStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"version": 1, "metrics": {}}

        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            if self.path.exists():
                corrupted = self.path.with_name(
                    f"{self.path.stem}.corrupt.{int(time.time())}{self.path.suffix}"
                )
                os.replace(self.path, corrupted)
            return {"version": 1, "metrics": {}}

        if not isinstance(payload, dict):
            return {"version": 1, "metrics": {}}
        payload.setdefault("version", 1)
        payload.setdefault("metrics", {})
        return payload

    def save(self, state: dict[str, Any]) -> None:
        write_json_atomic(self.path, state)


class JsonlWriter:
    def __init__(self, path: Path, max_bytes: int) -> None:
        self.path = path
        self.max_bytes = max_bytes

    def append(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._rotate_if_needed()
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n")

    def _rotate_if_needed(self) -> None:
        try:
            size = self.path.stat().st_size
        except FileNotFoundError:
            return
        if size < self.max_bytes:
            return
        backup = self.path.with_suffix(f"{self.path.suffix}.1")
        os.replace(self.path, backup)
