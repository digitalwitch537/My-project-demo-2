from __future__ import annotations

import logging
import os
from pathlib import Path

import uvicorn

from app.analyzer import Analyzer
from app.api import create_app
from app.config import load_config
from app.notifier import SlackNotifier
from app.queue import AnalysisWorker
from app.storage import JobStore


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    config_path = Path(
        os.getenv("AI_MODEL_CONFIG", Path(__file__).resolve().parent / "config.yml")
    )
    config = load_config(config_path)
    store = JobStore(config.data_dir)
    analyzer = Analyzer(config)
    notifier = SlackNotifier(
        webhook_url=config.slack.webhook_url,
        enabled=config.slack.enabled,
        dry_run=config.slack.dry_run,
        timeout_seconds=config.slack.timeout_seconds,
        channel=config.slack.channel,
        grafana_root_url=config.grafana_root_url,
    )
    worker = AnalysisWorker(config, store, analyzer, notifier)
    app = create_app(config, store, worker)

    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )


if __name__ == "__main__":
    main()
