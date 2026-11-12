"""Look up resort coordinates with the Nominatim (OpenStreetMap) API.

Results are cached in ``data/cache/geocodes.json``, keyed by the query
string. Each resort is only fetched once; editing a resort's
``geocode_query`` in ``resorts.csv`` makes it fetch again automatically.

Run directly to build or refresh the cache:
    python -m src.geocode
"""

import logging
import time

import pandas as pd
import requests

from src import config
from src.cache import load_json, save_json

logger = logging.getLogger(__name__)


def fetch_coordinates(query: str) -> dict | None:
    """Ask Nominatim for the best match to ``query``.

    Retries on timeouts and server errors. Returns a dict with ``lat``,
    ``lon`` and ``display_name``, or ``None`` if nothing matched or every
    attempt failed.
    """
    params = {"q": query, "format": "json", "limit": 1}
    headers = {"User-Agent": config.USER_AGENT}

    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            response = requests.get(
                config.NOMINATIM_URL,
                params=params,
                headers=headers,
                timeout=config.REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            matches = response.json()
            if not matches:
                return None
            best = matches[0]
            return {
                "lat": float(best["lat"]),
                "lon": float(best["lon"]),
                "display_name": best["display_name"],
            }
        except requests.RequestException as error:
            logger.warning("Attempt %d/%d failed for %r: %s", attempt, config.MAX_RETRIES, query, error)
            # Wait longer after each failure (2s, 4s, ...) before retrying.
            time.sleep(2 * attempt)

    return None


def is_within_state(lat: float, lon: float, state: str) -> bool:
    """Return True if the point falls inside the rough bounding box for ``state``."""
    min_lat, max_lat, min_lon, max_lon = config.STATE_BOUNDS[state]
    return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon


def geocode_resorts(resorts: pd.DataFrame) -> pd.DataFrame:
    """Add ``lat``, ``lon`` and ``geocode_status`` columns to the resort table.

    ``geocode_status`` is one of:
      - ``"ok"``: coordinates found and inside the expected state
      - ``"not_found"``: Nominatim returned no match (lat/lon left empty)
      - ``"outside_state"``: match was outside the state (lat/lon left empty)

    Failed lookups are not cached, so they are retried on the next run.
    """
    cache = load_json(config.GEOCODE_CACHE, default={})
    lats, lons, statuses = [], [], []

    for resort in resorts.itertuples():
        query = resort.geocode_query

        if query not in cache:
            logger.info("Geocoding %s ...", resort.resort)
            result = fetch_coordinates(query)
            time.sleep(config.NOMINATIM_DELAY_SECONDS)  # respect the rate limit
            if result is not None:
                cache[query] = result
                save_json(config.GEOCODE_CACHE, cache)  # save as we go

        result = cache.get(query)
        if result is None:
            status = "not_found"
        elif not is_within_state(result["lat"], result["lon"], resort.state):
            status = "outside_state"
        else:
            status = "ok"

        if status == "ok":
            lats.append(result["lat"])
            lons.append(result["lon"])
        else:
            logger.warning("%s: %s (query: %r)", resort.resort, status, query)
            lats.append(None)
            lons.append(None)
        statuses.append(status)

    return resorts.assign(lat=lats, lon=lons, geocode_status=statuses)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    table = geocode_resorts(pd.read_csv(config.RESORTS_CSV))
    print(table[["resort", "state", "lat", "lon", "geocode_status"]].to_string(index=False))
    print(f"\n{(table.geocode_status == 'ok').sum()} of {len(table)} resorts geocoded.")
