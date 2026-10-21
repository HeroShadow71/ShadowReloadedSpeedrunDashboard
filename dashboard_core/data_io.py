"""
Data loading and persistence for the dashboard.

Handles the full data-loading chain for a given game: local CSV, Supabase
cloud cache, and the Speedrun.com API as the final fallback, with a
cooldown-guarded manual refresh path that keeps all three in sync.
"""
import logging
import os
from time import time, sleep

import streamlit as st
import pandas as pd
from supabase import create_client

from constants import COOLDOWN_SECONDS
from dashboard_core.processing_runs import process_runs
from dashboard_core.io_utils import (
    get_last_refresh, set_last_refresh,
    game_cache_dir, game_processed_file,
)


def get_supabase_client():
    """Initialise Supabase safely. Mandatory try/except for portable use."""
    url, key = None, None
    try:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
    except Exception:
        pass

    if not url or not key:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        return None

    try:
        return create_client(url, key)
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def pull_from_supabase(config):
    """Fetch all runs for a game from cloud. Returns empty DF if no keys/connection.

    :param config: GameConfig instance
    :return: DataFrame of runs for this game
    """
    supabase = get_supabase_client()
    if not supabase:
        return pd.DataFrame()

    table_name = f"{config.key}_runs"
    try:
        all_data, offset, page_size = [], 0, 1000
        while True:
            response = supabase.table(table_name).select("*").range(offset, offset + page_size - 1).execute()
            all_data.extend(response.data)
            if len(response.data) < page_size: break
            offset += page_size
        df = pd.DataFrame(all_data)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df["submitted"] = pd.to_datetime(df["submitted"])
        return df
    except Exception:
        return pd.DataFrame()


def save_to_supabase(df, config):
    """Upload a game's runs to cloud, logging failures and returning False.

    :param df: processed runs DataFrame to upload
    :param config: GameConfig instance
    :return: True on success, False otherwise
    """
    supabase = get_supabase_client()
    if not supabase: return False

    try:
        table_name = f"{config.key}_runs"
        df_cloud = df.copy()
        for col in ["date", "submitted"]:
            if col in df_cloud.columns:
                df_cloud[col] = df_cloud[col].dt.strftime('%Y-%m-%dT%H:%M:%S')

        df_cloud = df_cloud.where(pd.notnull(df_cloud), None)
        supabase.table(table_name).upsert(df_cloud.to_dict(orient="records")).execute()
        pull_from_supabase.clear(config)

        return True
    except Exception:
        logging.exception("Failed to upload runs to Supabase table %s", table_name)
        return False


@st.cache_data(show_spinner="Fetching data from Speedrun.com API...")
def fetch_api_data_cached(config):
    """RAM-based cache for portable users to prevent repeated API hits.

    :param config: GameConfig instance
    :return: processed runs DataFrame for this game
    """
    return process_runs(config)


def get_data(config, force_refresh=False):
    """
    Load a game's runs via the fallback chain (local CSV, Supabase, API),
    or force a full refresh across all three.

    :param config: GameConfig instance
    :param force_refresh: if True, re-fetch from the API and resync Supabase/CSV
    :return: DataFrame of runs for this game
    """
    now = time()
    cache_dir = game_cache_dir(config)
    last_refresh_file = cache_dir / "last_refresh.json"
    processed_file = game_processed_file(config)

    last_refresh = get_last_refresh(last_refresh_file) or 0
    cooldown_remaining = COOLDOWN_SECONDS - (now - last_refresh)
    is_on_cloud = os.environ.get("STREAMLIT_CLOUD_DEPLOYMENT") == "true"

    if force_refresh and cooldown_remaining > 0:
        st.info(f"Data was refreshed recently. Please wait {int(cooldown_remaining)}s.")
        return get_data(config, force_refresh=False)

    if force_refresh:
        pull_from_supabase.clear(config)
        fetch_api_data_cached.clear(config)

        with st.spinner("Refreshing all data sources..."):
            old_df = pull_from_supabase(config)
            if old_df.empty and processed_file.exists():
                old_df = pd.read_csv(processed_file)
            old_ids = set(old_df["id"]) if not old_df.empty else set()

            df = process_runs(config)
            sync_success = save_to_supabase(df, config)

            if not is_on_cloud:
                processed_file.parent.mkdir(parents=True, exist_ok=True)
                df.to_csv(processed_file, index=False)

        set_last_refresh(last_refresh_file, now)
        st.session_state[f"last_refresh_time_{config.key}"] = now

        added = len(set(df["id"]) - old_ids) if not df.empty else 0
        st.success(f"Updated ({'Cloud' if sync_success else 'Local'}) - {added} new runs!")
        sleep(2)
        st.rerun()

    if not is_on_cloud and processed_file.exists():
        return pd.read_csv(processed_file, index_col=False, parse_dates=["date", "submitted"])

    df_cloud = pull_from_supabase(config)
    if not df_cloud.empty:
        return df_cloud

    df_api = fetch_api_data_cached(config)

    if not is_on_cloud and not processed_file.exists():
        try:
            processed_file.parent.mkdir(parents=True, exist_ok=True)
            df_api.to_csv(processed_file, index=False)
        except Exception: pass

    return df_api