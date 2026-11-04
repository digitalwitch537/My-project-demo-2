from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


class AiModelClient:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": "mern-aiops/1.0"})

    def trigger(self, payload: dict[str, Any]) -> bool:
        try:
            response = self.session.post(
                f"{self.base_url}/analyze",
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("AI model trigger failed: %s", exc)
            return False
        return True
