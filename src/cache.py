"""Small helpers for reading and writing local cache files.

All file I/O for cached API results goes through here, so caching works
the same way everywhere in the project.
"""

import json
from pathlib import Path
from typing import Any


def load_json(path: Path, default: Any = None) -> Any:
    """Return the parsed contents of a JSON file, or ``default`` if it doesn't exist."""
    if not path.exists():
        return default
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    """Write ``data`` to a JSON file, creating parent folders if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
