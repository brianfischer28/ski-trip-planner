"""Project-wide settings: file paths, API endpoints, and constants.

Keeping these in one place means the rest of the code never hard-codes
a URL or a file path.
"""

from pathlib import Path

# --- Paths -----------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"

RESORTS_CSV = DATA_DIR / "resorts.csv"
GEOCODE_CACHE = CACHE_DIR / "geocodes.json"
ELEVATION_CACHE = CACHE_DIR / "elevation.json"

# --- HTTP ------------------------------------------------------------------

# Nominatim's usage policy requires a User-Agent that identifies the app.
USER_AGENT = "ski-trip-planner/0.1 (https://github.com/brianfischer28/ski-trip-planner)"
REQUEST_TIMEOUT_SECONDS = 30
MAX_RETRIES = 3

# --- Nominatim (geocoding) -------------------------------------------------

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_DELAY_SECONDS = 1.1  # policy limit is 1 request/second

# Rough bounding boxes used to sanity-check geocoding results:
# (min_lat, max_lat, min_lon, max_lon)
STATE_BOUNDS = {
    "CO": (36.9, 41.1, -109.1, -102.0),
    "UT": (36.9, 42.1, -114.1, -109.0),
}

# --- Open-Meteo (elevation and weather) ------------------------------------

ELEVATION_URL = "https://api.open-meteo.com/v1/elevation"

# Every resort in the seed file has a base above this. A geocoded point
# below it probably landed in a valley town instead of at the resort.
MIN_RESORT_ELEVATION_M = 1800
