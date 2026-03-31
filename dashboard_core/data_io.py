"""
Data loading and cloud synchronization helpers.

This module provides utilities to:
- Fetch processed run data from the Supabase cloud database
- Push fresh API data to the cloud
- Handle local CSV fallbacks for development
- Manage refresh cooldowns and UI feedback
"""
import logging
import os
from time import time, sleep
from pathlib import Path

import streamlit as st
import pandas as pd
from supabase import create_client

from constants import DATA_FILE, COOLDOWN_SECONDS, PROCESSED_DIR
from dashboard_core.processing_runs import process_runs
from dashboard_core.io_utils import get_global_last_refresh, set_global_last_refresh


def get_supabase_client():
    """
    Initialise the Supabase client using secrets or environment variables.

    Checks Streamlit secrets first (for Cloud Dashboard), then falls back 
    to environment variables (for GitHub Actions and local development).

    :return: Supabase Client instance
    :raises ValueError: If credentials are missing
    """
    url = st.secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY") or os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        logging.error("Supabase credentials missing from secrets/env")
        raise ValueError("Supabase credentials not found")
        
    return create_client(url, key)


def save_to_supabase(df):
    """
    Upload or update processed runs in the cloud database.

    Cleans NaN values and converts datetimes to ISO strings for JSON 
    compatibility before performing an upsert operation.

    :param df: DataFrame of processed runs to upload
    :return: bool True if successful, False otherwise
    """
    try:
        supabase = get_supabase_client()
        
        # Prepare data for JSON serialization
        df_cloud = df.copy()
        for col in ["date", "submitted"]:
            if col in df_cloud.columns:
                # Convert to ISO string format
                df_cloud[col] = df_cloud[col].dt.strftime('%Y-%m-%dT%H:%M:%S')
        
        # Replace Pandas NaN with Python None (JSON null) to prevent serialization errors
        df_cloud = df_cloud.where(pd.notnull(df_cloud), None)
        
        data_dict = df_cloud.to_dict(orient="records")
        
        # Upsert matches on the 'id' primary key defined in Supabase
        supabase.table("shadow_reloaded_runs").upsert(data_dict).execute()
        logging.info("Successfully synced %d runs to Supabase", len(data_dict))
        return True
    except Exception as e:
        logging.exception("Failed to sync data to Supabase")
        return False


@st.cache_data(ttl=3600, show_spinner=False)
def pull_from_supabase():
    """
    Fetch all runs from the cloud database and restore datatypes.

    :return: DataFrame of all runs stored in the cloud
    """
    try:
        supabase = get_supabase_client()
        response = supabase.table("shadow_reloaded_runs").select("*").execute()
        df = pd.DataFrame(response.data)
        
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df["submitted"] = pd.to_datetime(df["submitted"])
        return df
    except Exception as e:
        logging.exception("Failed to fetch data from Supabase")
        raise e


def get_data(force_refresh=False):
    """
    Return processed runs, optionally forcing a refresh from the API.

    When `force_refresh` is True, this function:
    1. Fetches fresh data from Speedrun.com API
    2. Pushes the updated data to Supabase
    3. Updates the local CSV if running in a local environment
    
    Otherwise, it pulls the latest data from the cloud database.

    :param force_refresh: Force a refresh from API and sync to cloud.
    :return: `df`, processed runs as a DataFrame
    """
    now = time()
    last_refresh = get_global_last_refresh() or 0
    cooldown_remaining = COOLDOWN_SECONDS - (now - last_refresh)

    # Respect cooldown when requested
    if force_refresh and cooldown_remaining > 0:
        st.info(
            "Data was refreshed recently."
            f" Please wait {int(cooldown_remaining)}s before refreshing again."
        )
        return pull_from_supabase()

    # Refresh from API and sync to Cloud
    if force_refresh:
        with st.spinner("Fetching and syncing fresh data..."):
            try:
                # Determine old IDs to calculate the 'added' count
                old_df = pull_from_supabase()
                old_ids = set(old_df["id"]) if not old_df.empty else set()
            except Exception:
                old_ids = set()

            # Clear cache and fetch fresh runs
            pull_from_supabase.clear()
            df = process_runs()
            
            # Sync to Supabase
            save_to_supabase(df)

            # Update local CSV for development speed (if not on Streamlit Cloud)
            if not os.environ.get("STREAMLIT_CLOUD_DEPLOYMENT"):
                Path(PROCESSED_DIR).mkdir(parents=True, exist_ok=True)
                df.to_csv(DATA_FILE, index=False)

        # Persist the last-refresh timestamp
        try:
            set_global_last_refresh(now)
        except Exception as e:
            logging.warning("Failed to persist last refresh timestamp: %s", e)

        st.session_state["last_refresh_time"] = now

        # Compute how many new runs were added
        try:
            new_ids = set(df["id"])
            added = len(new_ids - old_ids)
        except Exception:
            added = None

        # Show result message
        if added is None:
            success_msg = st.success("Data updated successfully!")
        elif added == 0:
            success_msg = st.info("Data refreshed - no new runs were added.")
        else:
            success_msg = st.success(f"Data refreshed - {added} new runs added to Cloud!")

        sleep(4)
        success_msg.empty()
        return df

    # Default Load: Use local CSV if available locally, otherwise pull from Cloud
    if not os.environ.get("STREAMLIT_CLOUD_DEPLOYMENT") and DATA_FILE.exists():
        return pd.read_csv(DATA_FILE, index_col=False, parse_dates=["date", "submitted"])
    
    return pull_from_supabase()
