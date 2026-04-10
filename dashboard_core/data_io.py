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
def pull_from_supabase():
    """Fetch all runs from cloud. Returns empty DF if no keys/connection."""
    supabase = get_supabase_client()
    if not supabase:
        return pd.DataFrame()

    try:
        all_data, offset, page_size = [], 0, 1000
        while True:
            response = supabase.table("shadow_reloaded_runs").select("*").range(offset, offset + page_size - 1).execute()
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

def save_to_supabase(df):
    """Uploads to cloud. Returns False silently if no keys."""
    supabase = get_supabase_client()
    if not supabase: return False
    try:
        df_cloud = df.copy()
        for col in ["date", "submitted"]:
            if col in df_cloud.columns:
                df_cloud[col] = df_cloud[col].dt.strftime('%Y-%m-%dT%H:%M:%S')
        df_cloud = df_cloud.where(pd.notnull(df_cloud), None)
        supabase.table("shadow_reloaded_runs").upsert(df_cloud.to_dict(orient="records")).execute()
        pull_from_supabase.clear()
        return True
    except Exception:
        return False

@st.cache_data(show_spinner="Fetching data from Speedrun.com API...")
def fetch_api_data_cached():
    """RAM-based cache for portable users to prevent repeated API hits."""
    return process_runs()

def get_data(force_refresh=False):
    now = time()
    last_refresh = get_global_last_refresh() or 0
    cooldown_remaining = COOLDOWN_SECONDS - (now - last_refresh)
    is_on_cloud = os.environ.get("STREAMLIT_CLOUD_DEPLOYMENT") == "true"

    # Cooldown Check
    if force_refresh and cooldown_remaining > 0:
        st.info(f"Data was refreshed recently. Please wait {int(cooldown_remaining)}s.")
        return get_data(force_refresh=False)

    # Manual Refresh Logic
    if force_refresh:
        pull_from_supabase.clear()
        fetch_api_data_cached.clear() # Clear the RAM cache
        
        with st.spinner("Refreshing all data sources..."):
            # Silent check for old data
            old_df = pull_from_supabase()
            if old_df.empty and DATA_FILE.exists():
                old_df = pd.read_csv(DATA_FILE)
            old_ids = set(old_df["id"]) if not old_df.empty else set()

            # Fetch fresh runs
            df = process_runs()
            sync_success = save_to_supabase(df)

            if not is_on_cloud:
                Path(PROCESSED_DIR).mkdir(parents=True, exist_ok=True)
                df.to_csv(DATA_FILE, index=False)

        set_global_last_refresh(now)
        st.session_state["last_refresh_time"] = now
        
        added = len(set(df["id"]) - old_ids) if not df.empty else 0
        st.success(f"Updated ({'Cloud' if sync_success else 'Local'}) - {added} new runs!")
        sleep(2)
        st.rerun()

    # Default Load Logic (The Fallback Chain)
    
    # Local CSV
    if not is_on_cloud and DATA_FILE.exists():
        return pd.read_csv(DATA_FILE, index_col=False, parse_dates=["date", "submitted"])
    
    # Supabase (Cloud default)
    df_cloud = pull_from_supabase()
    if not df_cloud.empty:
        return df_cloud
    
    # Portable Fallback (API + RAM Cache + Auto-Save)
    # This uses the cached function so the spinner only appears ONCE per session
    df_api = fetch_api_data_cached()
    
    # Auto-save CSV so the NEXT rerun uses it
    if not is_on_cloud and not DATA_FILE.exists():
        try:
            Path(PROCESSED_DIR).mkdir(parents=True, exist_ok=True)
            df_api.to_csv(DATA_FILE, index=False)
        except Exception: pass
        
    return df_api
