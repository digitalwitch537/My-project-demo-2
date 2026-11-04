from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from datetime import datetime, timezone
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


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} does not contain a JSON object")
    return payload


class JsonlWriter:
    def __init__(self, path: Path, max_bytes: int) -> None:
        self.path = path
        self.max_bytes = max_bytes
        self._lock = threading.Lock()

    def append(self, payload: dict[str, Any]) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._rotate_if_needed()
            with self.path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(
                    json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n"
                )

    def _rotate_if_needed(self) -> None:
        try:
            size = self.path.stat().st_size
        except FileNotFoundError:
            return
        if size < self.max_bytes:
            return
        backup = self.path.with_suffix(f"{self.path.suffix}.1")
        os.replace(self.path, backup)


class JobStore:
    def __init__(self, data_dir: Path) -> None:
        self.root = data_dir / "jobs"
        self.pending_dir = self.root / "pending"
        self.done_dir = self.root / "done"
        self.failed_dir = self.root / "failed"
        self._lock = threading.RLock()
        for directory in (self.pending_dir, self.done_dir, self.failed_dir):
            directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def job_id_for(event_id: str) -> str:
        return hashlib.sha256(event_id.encode("utf-8")).hexdigest()

    def enqueue(self, payload: dict[str, Any]) -> tuple[str, bool]:
        event_id = str(payload.get("event_id", "")).strip()
        if not event_id:
            raise ValueError("event_id is required")

        job_id = self.job_id_for(event_id)
        with self._lock:
            if self._existing_path(job_id) is not None:
                return job_id, False

            job = {
                "job_id": job_id,
                "event_id": event_id,
                "received_at": datetime.now(timezone.utc).isoformat(),
                "status": "pending",
                "payload": payload,
            }
            write_json_atomic(self.pending_dir / f"{job_id}.json", job)
        return job_id, True

    def next_pending(self) -> dict[str, Any] | None:
        with self._lock:
            paths = sorted(
                self.pending_dir.glob("*.json"),
                key=lambda path: path.stat().st_mtime,
            )
            for path in paths:
                job_id = path.stem
                if (self.done_dir / f"{job_id}.json").exists() or (
                    self.failed_dir / f"{job_id}.json"
                ).exists():
                    path.unlink(missing_ok=True)
                    continue
                try:
                    return read_json(path)
                except (OSError, ValueError, json.JSONDecodeError) as exc:
                    self._write_failed(
                        job_id,
                        {"job_id": job_id, "status": "failed"},
                        f"invalid queue file: {exc}",
                    )
                    path.unlink(missing_ok=True)
        return None

    def complete(self, job_id: str, result: dict[str, Any]) -> None:
        with self._lock:
            job = self._read_optional(self.pending_dir / f"{job_id}.json") or {
                "job_id": job_id,
                "status": "pending",
            }
            job["status"] = "done"
            job["completed_at"] = datetime.now(timezone.utc).isoformat()
            job["result"] = result
            write_json_atomic(self.done_dir / f"{job_id}.json", job)
            (self.pending_dir / f"{job_id}.json").unlink(missing_ok=True)

    def fail(self, job_id: str, error: str) -> None:
        with self._lock:
            job = self._read_optional(self.pending_dir / f"{job_id}.json") or {
                "job_id": job_id,
                "status": "pending",
            }
            self._write_failed(job_id, job, error)
            (self.pending_dir / f"{job_id}.json").unlink(missing_ok=True)

    def get(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            path = self._existing_path(job_id)
            return self._read_optional(path) if path is not None else None

    def pending_count(self) -> int:
        with self._lock:
            return sum(1 for _ in self.pending_dir.glob("*.json"))

    def _existing_path(self, job_id: str) -> Path | None:
        for directory in (self.pending_dir, self.done_dir, self.failed_dir):
            path = directory / f"{job_id}.json"
            if path.exists():
                return path
        return None

    def _write_failed(
        self,
        job_id: str,
        job: dict[str, Any],
        error: str,
    ) -> None:
        failed = dict(job)
        failed["status"] = "failed"
        failed["failed_at"] = datetime.now(timezone.utc).isoformat()
        failed["error"] = error
        write_json_atomic(self.failed_dir / f"{job_id}.json", failed)

    @staticmethod
    def _read_optional(path: Path | None) -> dict[str, Any] | None:
        if path is None or not path.exists():
            return None
        try:
            return read_json(path)
        except (OSError, ValueError, json.JSONDecodeError):
            return None
