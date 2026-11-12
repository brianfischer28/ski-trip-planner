"""Clients for the Open-Meteo APIs (elevation now; historical and forecast later).

Open-Meteo is free and needs no API key. Results are cached under
``data/cache/`` so the app doesn't refetch them on every run.

Run directly to build or refresh the elevation cache:
    python -m src.weather
"""

import logging

import pandas as pd

from src import config
from src.cache import load_json, save_json
from src.http_client import get_json

logger = logging.getLogger(__name__)


def _point_key(lat: float, lon: float) -> str:
    """Cache key for a coordinate, e.g. ``"39.5995,-106.3395"``.

    Keying by coordinate (not resort name) means a resort whose geocode
    changes gets a fresh elevation automatically.
    """
    return f"{lat:.4f},{lon:.4f}"


def fetch_elevations(points: list[tuple[float, float]]) -> list[float | None] | None:
    """Look up elevation in meters for many (lat, lon) points in one request.

    Returns one value per point (in the same order), or ``None`` if the
    request failed after retries.
    """
    params = {
        "latitude": ",".join(f"{lat:.4f}" for lat, _ in points),
        "longitude": ",".join(f"{lon:.4f}" for _, lon in points),
    }
    data = get_json(config.ELEVATION_URL, params)
    if not data or "elevation" not in data:
        return None
    return data["elevation"]


def add_elevation(resorts: pd.DataFrame) -> pd.DataFrame:
    """Add ``elevation_m`` and ``elevation_status`` columns to the resort table.

    Expects the ``lat``/``lon`` columns from ``geocode.geocode_resorts``.
    ``elevation_status`` is one of:
      - ``"ok"``: elevation found and at or above ``MIN_RESORT_ELEVATION_M``
      - ``"below_min"``: suspiciously low, probably a bad geocode (value kept)
      - ``"missing"``: no coordinates, or the API returned no value
    """
    cache = load_json(config.ELEVATION_CACHE, default={})
    has_coords = resorts["lat"].notna() & resorts["lon"].notna()
    points = list(zip(resorts.loc[has_coords, "lat"], resorts.loc[has_coords, "lon"]))

    # Fetch every uncached point in a single batched request.
    to_fetch = [p for p in points if _point_key(*p) not in cache]
    if to_fetch:
        logger.info("Fetching elevation for %d points ...", len(to_fetch))
        values = fetch_elevations(to_fetch)
        if values is None:
            logger.error("Elevation request failed; those resorts will be marked missing.")
        else:
            for point, value in zip(to_fetch, values):
                if value is not None:
                    cache[_point_key(*point)] = value
            save_json(config.ELEVATION_CACHE, cache)

    elevations, statuses = [], []
    for row in resorts.itertuples():
        value = cache.get(_point_key(row.lat, row.lon)) if pd.notna(row.lat) and pd.notna(row.lon) else None
        if value is None:
            status = "missing"
        elif value < config.MIN_RESORT_ELEVATION_M:
            status = "below_min"
        else:
            status = "ok"
        if status != "ok":
            logger.warning("%s: elevation %s (%s m)", row.resort, status, value)
        elevations.append(value)
        statuses.append(status)

    return resorts.assign(elevation_m=elevations, elevation_status=statuses)


if __name__ == "__main__":
    from src.geocode import geocode_resorts

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    table = add_elevation(geocode_resorts(pd.read_csv(config.RESORTS_CSV)))
    print(table[["resort", "state", "lat", "lon", "elevation_m", "elevation_status"]].to_string(index=False))
    print(f"\n{(table.elevation_status == 'ok').sum()} of {len(table)} resorts have a valid elevation.")
