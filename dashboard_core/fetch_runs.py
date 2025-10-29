"""
Fetch and cache verified runs from Speedrun.com.

Retrieves verified runs from the API, falling back to a local cache
when unavailable.
"""
import logging

from dashboard_core.api_client import ApiClient
from dashboard_core.io_utils import safe_read_json, safe_write_json
from constants import GAME_ID, CACHE_FILE


def fetch_verified_runs():
    """
    Return verified runs, using a local cache as fallback.

    :raises RuntimeError: if neither the API nor local cache yield any verified
        runs
    :return: a list of verified run dictionaries
    """
    existing_runs = safe_read_json(CACHE_FILE, default=[])

    client = ApiClient()
    last_exc = None
    try:
        # Disable caching to prevent saving unverified runs to cache
        fetched_runs = client.get_all_runs(GAME_ID, cache_file=None)
    except Exception as e:
        last_exc = e
        logging.warning("Failed to fetch runs from API, falling back to cache: %s", e)
        fetched_runs = []

    # Merge sources and keep only verified runs
    combined = {run["id"]: run for run in (existing_runs + fetched_runs)}
    verified_runs = [r for r in combined.values() if r.get("status", {}).get("status") == "verified"]

    safe_write_json(CACHE_FILE, verified_runs)

    if not verified_runs and not existing_runs:
        msg = "Failed to obtain verified runs from API"
        if last_exc is not None:
            msg = f"{msg}: {last_exc}"
        raise RuntimeError(msg)

    if not verified_runs and existing_runs:
        return existing_runs

    return verified_runs
