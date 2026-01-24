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
    NOTE_KEY, CHARACTER_KEY, UNLOCK_RIFLE_VAR_MAP, STORY_MODE_ENDING_MAP,
    STORY_MODE_ENDING_VAR_ID, UNLOCK_RIFLE_RULESET_VAR_ID
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
        "story_mode_ending", "unlock_rifle_ruleset"
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
                "submitted": run["submitted"],
                "story_mode_ending": run["values"].get(STORY_MODE_ENDING_VAR_ID),
                "unlock_rifle_ruleset": run["values"].get(UNLOCK_RIFLE_RULESET_VAR_ID)
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

    # Map subcategory IDs to readable names
    df["subcategory_name"] = pd.NA
    df.loc[df["story_mode_ending"].notna(), "subcategory_name"] = df.loc[df["story_mode_ending"].notna(), "story_mode_ending"].map(STORY_MODE_ENDING_MAP)
    df.loc[df["unlock_rifle_ruleset"].notna(), "subcategory_name"] = df.loc[df["unlock_rifle_ruleset"].notna(), "unlock_rifle_ruleset"].map(UNLOCK_RIFLE_VAR_MAP)
    
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
        
        # Get Story Mode and Unlock Shadow Rifle category IDs from the categories list
        story_mode_id = next((cat["id"] for cat in categories if cat["name"] == "Story Mode"), None)
        unlock_rifle_id = next((cat["id"] for cat in categories if cat["name"] == "Unlock Shadow Rifle"), None)
        
        # Separate Story Mode/Unlock Shadow Rifle (with subcategories) from others
        mask_with_subcat = full_game_df["category"].isin([story_mode_id, unlock_rifle_id])
        
        # Process runs with subcategories (include subcategory_name in grouping)
        if mask_with_subcat.any():
            subcat_idx = full_game_df.index[mask_with_subcat]
            subcat_df = full_game_df.loc[subcat_idx].copy()
            mark_obsolete_and_place(subcat_df, ["category", "character", "subcategory_name"])
            full_game_df.loc[subcat_idx, ["obsolete", "place"]] = subcat_df[["obsolete", "place"]]
        
        # Process runs without subcategories (don't include subcategory_name)
        mask_no_subcat = ~mask_with_subcat
        if mask_no_subcat.any():
            no_subcat_idx = full_game_df.index[mask_no_subcat]
            no_subcat_df = full_game_df.loc[no_subcat_idx].copy()
            mark_obsolete_and_place(no_subcat_df, ["category", "character"])
            full_game_df.loc[no_subcat_idx, ["obsolete", "place"]] = no_subcat_df[["obsolete", "place"]]
        
        df.loc[full_game_idx, ["obsolete", "place"]] = full_game_df[["obsolete", "place"]]

    # Drop intermediate id columns
    df.drop(columns=["category", "level", "player_id", "character", "note", "story_mode_ending", "unlock_rifle_ruleset"], inplace=True)

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
