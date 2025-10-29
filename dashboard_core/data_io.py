"""
Data loading and caching helpers.

This module provides utilities to:
- Load processed run data from the local CSV cache
- Refresh data from the API when needed
- Handle heavy processing via `process_runs`
- Cache results with Streamlit's `st.cache_data`
"""
from time import time, sleep
import logging
from pathlib import Path

import streamlit as st
import pandas as pd

from constants import DATA_FILE, COOLDOWN_SECONDS, PROCESSED_DIR
from dashboard_core.processing_runs import process_runs
from dashboard_core.io_utils import get_global_last_refresh, set_global_last_refresh


@st.cache_data(show_spinner=False)
def load_and_cache():
    """
    Fetch, process and persist runs, returning a DataFrame.

    :return: `df` processed runs as a DataFrame
    """
    df = process_runs()
    # Ensure processed dir exists before writing the CSV
    Path(PROCESSED_DIR).mkdir(parents=True, exist_ok=True)
    df.to_csv(DATA_FILE, index=False)
    return df


def get_data(force_refresh=False):
    """
    Return processed runs, optionally forcing a refresh.

    When `force_refresh` is True, this function reloads data via
    `load_and_cache` and updates the global last-refresh timestamp.
    Respects a cooldown (`COOLDOWN_SECONDS`) to prevent excessive API calls.
    
    :param force_refresh: Force a refresh even if a cached CSV exists.
    :return: `df`, processed runs as a DataFrame
    """
    now = time()
    last_refresh = get_global_last_refresh() or 0
    cooldown_remaining = COOLDOWN_SECONDS - (now - last_refresh)

    # Respect cooldown when requested but allow first-time fetch if cache doesn't exist
    if force_refresh and cooldown_remaining > 0 and DATA_FILE.exists():
        st.info(
            "Data was refreshed recently."
            f" Please wait {int(cooldown_remaining)}s before refreshing again."
        )
        df = pd.read_csv(DATA_FILE, index_col=False, parse_dates=["date"])
        return df

    # Refresh or initial load
    if force_refresh or not DATA_FILE.exists():
        with st.spinner("Fetching and cleaning data..."):
            # Track previously cached run IDs to determine how many new runs were added
            try:
                old_ids = set()
                if DATA_FILE.exists():
                    old_df = pd.read_csv(DATA_FILE, index_col=False, parse_dates=["date"])
                    old_ids = set(old_df.get("id", []))
            except (pd.errors.EmptyDataError, pd.errors.ParserError, FileNotFoundError) as e:
                logging.warning("Failed to read existing data file %s: %s", DATA_FILE, e)

            # Clear cached Streamlit data and fetch fresh runs
            load_and_cache.clear()
            df = load_and_cache()

        # Persist the last-refresh timestamp (best-effort)
        try:
            set_global_last_refresh(now)
        except Exception as e:
            logging.warning("Failed to persist last refresh timestamp: %s", e)

        # Update in-memory session state for immediate UI feedback
        st.session_state["last_refresh_time"] = now

        # Compute how many new runs were added compared to the cached CSV
        try:
            new_ids = set(df.get("id", []))
            added = len(new_ids - old_ids) if old_ids else len(new_ids)
        except (AttributeError, TypeError, KeyError) as e:
            logging.warning("Failed to compute new run ids: %s", e)
            added = None

        # Show a concise refresh result message
        if added is None:
            success_msg = st.success("Data updated successfully!")
        elif added == 0:
            success_msg = st.info("Data refreshed - no new runs were added.")
        else:
            success_msg = st.success(f"Data refreshed - {added} new runs added.")

        sleep(4)
        success_msg.empty()
        return df

    df = pd.read_csv(DATA_FILE, index_col=False, parse_dates=["date"])
    return df
