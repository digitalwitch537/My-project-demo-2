from __future__ import annotations

import logging
import os
import signal
from pathlib import Path

from app.config import load_config
from app.service import AiopsService


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    config_path = Path(os.getenv("AIOPS_CONFIG", Path(__file__).resolve().parent / "config.yml"))
    config = load_config(config_path)
    service = AiopsService(config)

    def handle_stop(signum: int, frame: object) -> None:
        logging.getLogger(__name__).info("Received signal %s, stopping", signum)
        service.stop()

    signal.signal(signal.SIGTERM, handle_stop)
    signal.signal(signal.SIGINT, handle_stop)
    service.run_forever()


if __name__ == "__main__":
    main()
