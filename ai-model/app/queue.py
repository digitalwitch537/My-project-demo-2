from __future__ import annotations

import logging
import threading

from .analyzer import Analyzer
from .config import AppConfig
from .notifier import SlackNotifier
from .storage import JobStore, JsonlWriter

logger = logging.getLogger(__name__)


class AnalysisWorker:
    def __init__(
        self,
        config: AppConfig,
        store: JobStore,
        analyzer: Analyzer,
        notifier: SlackNotifier,
    ) -> None:
        self.config = config
        self.store = store
        self.analyzer = analyzer
        self.notifier = notifier
        self.analyses_writer = JsonlWriter(
            config.data_dir / "analyses.jsonl",
            5 * 1024 * 1024,
        )
        self.failures_writer = JsonlWriter(
            config.data_dir / "failures.jsonl",
            5 * 1024 * 1024,
        )
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(
            target=self._loop,
            name="ai-model-worker",
            daemon=True,
        )
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=10)

    def run_once(self) -> bool:
        job = self.store.next_pending()
        if job is None:
            return False

        job_id = str(job.get("job_id", "unknown"))
        try:
            result = self.analyzer.analyze(job)
            if result.get("status") == "analyzed":
                result["notification_sent"] = self.notifier.send_analysis(job, result)
            else:
                result["notification_sent"] = False
                result["notification_skipped_reason"] = "analysis_fallback"
                logger.warning(
                    "Skipped Slack RCA for job %s because the model analysis failed",
                    job_id,
                )
            self.store.complete(job_id, result)
            self.analyses_writer.append(result)
            logger.info("AI analysis completed for job %s", job_id)
        except Exception as exc:
            logger.exception("AI analysis failed for job %s", job_id)
            self.store.fail(job_id, str(exc))
            self.failures_writer.append(
                {
                    "job_id": job_id,
                    "failed_at": str(job.get("received_at", "")),
                    "error": str(exc),
                }
            )
        return True

    def _loop(self) -> None:
        logger.info(
            "AI-model worker started: poll=%ss model=%s",
            self.config.worker_poll_seconds,
            self.config.ollama.model,
        )
        while not self.stop_event.is_set():
            processed = self.run_once()
            if processed:
                continue
            self.stop_event.wait(self.config.worker_poll_seconds)
        logger.info("AI-model worker stopped")
