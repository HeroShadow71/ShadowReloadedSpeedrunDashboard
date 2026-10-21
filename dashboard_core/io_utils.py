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
    DATA_DIR, CACHE_DIR, PROCESSED_DIR
)


def ensure_project_dirs():
    """Create required project directories if missing."""
    for d in (DATA_DIR, CACHE_DIR, PROCESSED_DIR):
        Path(d).mkdir(parents=True, exist_ok=True)


def game_cache_dir(config):
    """
    Return the cache directory for a specific game.

    :param config: GameConfig instance
    :return: Path to this game's cache subfolder
    """
    return CACHE_DIR / config.key


def game_processed_file(config):
    """
    Return the processed-runs CSV path for a specific game.

    :param config: GameConfig instance
    :return: Path to this game's processed runs CSV
    """
    return PROCESSED_DIR / config.key / "runs_processed.csv"


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


def get_last_refresh(path):
    """
    Return last refresh epoch seconds, or `None` if unavailable.

    :param path: Path to the last-refresh JSON file to read
    :return: epoch seconds or `None`
    """
    data = safe_read_json(path, default=None)
    if isinstance(data, dict):
        try:
            return float(data.get("last_refresh"))
        except (TypeError, ValueError):
            return None
    return None


def set_last_refresh(path, ts):
    """
    Persist last refresh timestamp atomically.

    :param path: Path to the last-refresh JSON file to write
    :param float ts: epoch seconds to persist
    :return: True on success, False on error
    """
    tmp = path.with_suffix(".tmp")
    try:
        tmp.parent.mkdir(parents=True, exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"last_refresh": ts}, f)
        os.replace(tmp, path)
        return True

    except Exception as error:
        logging.warning("Failed to persist last refresh timestamp: %s", error)
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception as e:
            logging.warning("Failed to clean up temp file %s: %s", tmp, e)
        return False
