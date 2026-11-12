"""Shared HTTP helper: one place for timeouts, retries, and the User-Agent.

Every API client in the project (Nominatim, Open-Meteo) calls ``get_json``
instead of using ``requests`` directly, so network errors are handled the
same way everywhere.
"""

import logging
import time
from typing import Any

import requests

from src import config

logger = logging.getLogger(__name__)


def get_json(url: str, params: dict) -> Any | None:
    """GET ``url`` and return the parsed JSON body.

    Retries on timeouts, connection errors, and HTTP errors, waiting longer
    after each failure (2s, 4s, ...). Returns ``None`` if every attempt fails.
    """
    headers = {"User-Agent": config.USER_AGENT}

    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=config.REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            logger.warning("Attempt %d/%d failed for %s: %s", attempt, config.MAX_RETRIES, url, error)
            if attempt < config.MAX_RETRIES:
                time.sleep(2 * attempt)

    return None
