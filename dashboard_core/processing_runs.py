"""
Transforms the fetched run data into a cleaned DataFrame with computed places
and obsolescence flags. Creates/updates caches for players, categories, and levels.
"""
import logging

import pandas as pd

from constants import (
    GAME_ID,
    PLAYER_CACHE_FILE, CATEGORY_CACHE_FILE, LEVEL_CACHE_FILE,
    CHAR_MAP, NOTE_MAP,
    NOTE_KEY, CHARACTER_KEY,
)
from dashboard_core.fetch_runs import fetch_verified_runs
from dashboard_core.api_utils import fetch_api_cached
from dashboard_core.io_utils import safe_read_json, safe_write_json


def process_runs():
    """Fetch, normalize and rank verified runs.

    Creates/updates local caches for players, categories and levels.
    
    :return: `df` DataFrame containing all processed runs
    """
    verified_runs = fetch_verified_runs()

    # Define stable DataFrame schema for downstream logic and CSV export
    expected_cols = [
        "id", "weblink", "category", "level", "player_id",
        "date", "primary_t", "note", "character", "submitted",
    ]

    # Normalize API run objects into row dicts with the columns needed
    cleaned_runs = []
    for run in verified_runs:
        player_id = None
        players = run.get("players") or []
        if players:
            first = players[0]
            player_id = first.get("id")

        cleaned_runs.append(
            {
                "id": run["id"],
                "weblink": run["weblink"],
                "category": run["category"],
                "level": run.get("level"),
                "player_id": player_id,
                "date": run["date"],
                "primary_t": run["times"]["primary_t"],
                "note": run["values"][NOTE_KEY],
                "character": run["values"][CHARACTER_KEY],
                "submitted": run["submitted"]
            }
        )

    # Build DataFrame with stable column order
    df = pd.DataFrame(cleaned_runs, columns=expected_cols)

    categories_api = f"https://www.speedrun.com/api/v1/games/{GAME_ID}/categories"
    levels_api = f"https://www.speedrun.com/api/v1/games/{GAME_ID}/levels"

    try:
        categories = fetch_api_cached(categories_api, cache_file=CATEGORY_CACHE_FILE)
    except Exception as e:
        logging.exception("Failed to fetch categories from API")
        raise RuntimeError("Failed to load categories") from e

    try:
        levels = fetch_api_cached(levels_api, cache_file=LEVEL_CACHE_FILE)
    except Exception as e:
        logging.exception("Failed to fetch levels from API")
        raise RuntimeError("Failed to load levels") from e

    # Map category/level IDs into readable names
    df["category_name"] = df["category"].map({cat["id"]: cat["name"] for cat in categories})
    df["level_name"] = df["level"].map({lvl["id"]: lvl["name"] for lvl in levels})

    # Load player cache and lookup for missing display names
    player_map = safe_read_json(PLAYER_CACHE_FILE, default={}) or {}

    unique_player_ids = df["player_id"].dropna().unique()
    for p_id in unique_player_ids:
        if p_id not in player_map:
            try:
                user = fetch_api_cached(f"https://www.speedrun.com/api/v1/users/{p_id}", cache_file=None)
                names = user["names"]
                player_map[p_id] = names.get("international") or names.get("japanese")
            except Exception as e:
                logging.warning("Failed to fetch user %s, using ID as fallback: %s", p_id, e)
                player_map[p_id] = p_id

    safe_write_json(PLAYER_CACHE_FILE, player_map)

    # Convert ID columns to readable columns
    df["player_name"] = df["player_id"].map(player_map)
    df["character_name"] = df["character"].map(CHAR_MAP)
    df["note_name"] = df["note"].map(NOTE_MAP)

    # Prepare columns used by ranking logic
    df["place"] = pd.NA
    df["obsolete"] = False

    # Compute obsolescence and places for level runs
    mask_levels = df["level"].notna()
    if mask_levels.any():
        lvl_idx = df.index[mask_levels]
        lvl_df = df.loc[lvl_idx].copy()
        mark_obsolete_and_place(lvl_df, ["level", "category", "character"])
        df.loc[lvl_idx, ["obsolete", "place"]] = lvl_df[["obsolete", "place"]]

    # Compute obsolescence and places for full-game runs
    mask_full_game = df["level"].isna()
    if mask_full_game.any():
        full_game_idx = df.index[mask_full_game]
        full_game_df = df.loc[full_game_idx].copy()
        mark_obsolete_and_place(full_game_df, ["category", "character"])
        df.loc[full_game_idx, ["obsolete", "place"]] = full_game_df[["obsolete", "place"]]

    # Drop intermediate id columns
    df.drop(columns=["category", "level", "player_id", "character", "note"], inplace=True)

    # Ensure 'date' and 'submitted' are datetimelike
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["submitted"] = pd.to_datetime(df["submitted"], errors="coerce")

    return df


def mark_obsolete_and_place(df, groupby_cols):
    """Mark obsolete runs and assign places in-place.

    Compatibility wrapper that delegates to internal helpers. Mutates `df`.
   
    :param df: DataFrame
    :param groupby_cols: iterable of column names used for grouping
    """
    _mark_obsolete_runs(df, groupby_cols)
    _assign_ranking(df, groupby_cols)


def _mark_obsolete_runs(df, groupby_cols):
    """Mark runs that are not the player's best as obsolete for each note.
    
    :param df: DataFrame
    :param groupby_cols: columns to group by
    """
    keys = list(groupby_cols) + ["player_id", "note"]

    best = df.groupby(keys)["primary_t"].transform("min")
    df["obsolete"] = df["primary_t"] != best


def _assign_ranking(df, groupby_cols):
    """Assign integer competition places among non-obsolete runs.
    
    :param df: DataFrame
    :param groupby_cols: columns to group by
    """
    mask = ~df["obsolete"]
    
    ranks = df.loc[mask].groupby(groupby_cols)["primary_t"].rank(
        method="min", ascending=True
    ).astype("Int64")
    
    df.loc[mask, "place"] = ranks
