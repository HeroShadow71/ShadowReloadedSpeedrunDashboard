"""
Provides safe I/O helpers and directory management utilities.

Ensures project directories exist, handles JSON reading/writing with error recovery
and manages the global last-refresh timestamp file.
"""
import json
from pathlib import Path
import os
import logging

from constants import (
    DATA_DIR, CACHE_DIR, PROCESSED_DIR, LAST_REFRESH_FILE
)


def ensure_project_dirs():
    """Create required project directories if missing."""
    for d in (DATA_DIR, CACHE_DIR, PROCESSED_DIR):
        Path(d).mkdir(parents=True, exist_ok=True)


def safe_read_json(path, default=None):
    """
    Read JSON from `path` and return `default` on error.

    :param path: Path-like object pointing to a JSON file
    :param default: value to return on error
    :return: parsed JSON or `default`
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default
    except Exception as e:
        logging.warning("Unexpected error reading JSON %s: %s", path, e)
        return default


def safe_write_json(path, data):
    """
    Write `data` as JSON to `path`.

    :param path: Path-like object where JSON will be written
    :param data: data to serialize as JSON
    :return: True on success, False on error
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        return True
    except OSError as e:
        logging.warning("Failed to write JSON to %s: %s", path, e)
        return False


def get_global_last_refresh():
    """Return last refresh epoch seconds, or `None` if unavailable.

    Reads the JSON file written by the `set_global_last_refresh` function.

    :return: epoch seconds or `None`
    """
    data = safe_read_json(LAST_REFRESH_FILE, default=None)
    if isinstance(data, dict):
        try:
            # Convert stored value to float, return None if missing or invalid
            return float(data.get("last_refresh"))
        except (TypeError, ValueError):
            return None
    return None


def set_global_last_refresh(ts):
    """
    Persist last refresh timestamp atomically.

    :param float ts: epoch seconds to persist
    :return: True on success, False on error
    """
    tmp = LAST_REFRESH_FILE.with_suffix(".tmp")
    try:
        tmp.parent.mkdir(parents=True, exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"last_refresh": ts}, f)
        # Write to a temporary file and replace original atomically to prevent partial writes
        os.replace(tmp, LAST_REFRESH_FILE)
        return True
    
    except Exception as error:
        logging.warning("Failed to persist last refresh timestamp: %s", error)
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception as e:
            logging.warning("Failed to clean up temp file %s: %s", tmp, e)
        return False
