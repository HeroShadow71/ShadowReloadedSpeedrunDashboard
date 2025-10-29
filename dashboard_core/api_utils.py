"""
HTTP fetch utilities with retry and optional local cache fallback.

Provides `fetch_api_cached` for resilient API requests with exponential backoff
and file-based caching.
"""
import json
import time
import logging

import requests

from constants import API_TIMEOUT


def fetch_api_cached(
    url,
    cache_file=None,
    timeout=None,
    max_retries=2,
    backoff_sec=2.0,
):
    """
    Fetch JSON from `url` with retries and optional cache fallback.

    :param url: API endpoint URL
    :param cache_file: Optional Path to write/read cached data
    :param timeout: Request timeout in seconds (defaults to `constants.API_TIMEOUT`)
    :param max_retries: Number of retries on failure
    :param backoff_sec: Exponential backoff base for retries
    :return: Parsed JSON payload (the `"data"` field if present, else the full object)
    :raises RequestException: If all requests fail and no valid cache is available
    """
    timeout = timeout or API_TIMEOUT
    last_exc = None

    # Attempt the request with retries and exponential backoff
    for attempt in range(max_retries + 1):
        try:
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()
            payload = resp.json()
            data = payload.get("data", payload)

            if cache_file and data is not None:
                try:
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                except OSError as e:
                    logging.warning("Failed to write API cache %s: %s", cache_file, e)
            return data

        except requests.RequestException as e:
            last_exc = e
            # Respect Retry-After
            if hasattr(e, "response") and e.response is not None and e.response.status_code == 429:
                try:
                    retry_after = int(e.response.headers.get("Retry-After", 1))
                except Exception:
                    retry_after = 1
                time.sleep(retry_after)
            else:
                time.sleep(backoff_sec * (attempt + 1))

    # No successful fetch, try cache fallback
    if cache_file and cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logging.warning("Failed to read API cache %s: %s", cache_file, e)

    # Fetch and cache failed
    raise RuntimeError(f"Failed to fetch {url}") from last_exc
