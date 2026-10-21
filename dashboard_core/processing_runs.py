"""
Transforms the fetched run data into a cleaned DataFrame with computed places
and obsolescence flags. Creates/updates caches for players, categories, and levels.
"""
import logging

import pandas as pd

from dashboard_core.fetch_runs import fetch_verified_runs
from dashboard_core.api_utils import fetch_api_cached
from dashboard_core.io_utils import safe_read_json, safe_write_json, game_cache_dir

# Sentinel used when a game has no character/note variable, so grouping logic
# always has a non-null, constant key to group on instead of a dropped NaN.
NO_CHARACTER = ""
NO_NOTE = ""


def process_runs(config):
    """Fetch, normalize and rank verified runs for a given game.

    Creates/updates local caches for players, categories and levels.

    :param config: GameConfig instance for the game being processed
    :return: `df` DataFrame containing all processed runs
    """
    cache_dir = game_cache_dir(config)
    verified_runs = fetch_verified_runs(config.game_id, cache_dir / "runs_cache.json")

    categories_api = f"https://www.speedrun.com/api/v1/games/{config.game_id}/categories"
    levels_api = f"https://www.speedrun.com/api/v1/games/{config.game_id}/levels"

    try:
        categories = fetch_api_cached(categories_api, cache_file=cache_dir / "categories_cache.json")
    except Exception as e:
        logging.exception("Failed to fetch categories from API")
        raise RuntimeError("Failed to load categories") from e

    try:
        levels = fetch_api_cached(levels_api, cache_file=cache_dir / "levels_cache.json")
    except Exception as e:
        logging.exception("Failed to fetch levels from API")
        raise RuntimeError("Failed to load levels") from e

    category_name_by_id = {cat["id"]: cat["name"] for cat in categories}
    level_name_by_id = {lvl["id"]: lvl["name"] for lvl in levels}

    # Define stable DataFrame schema for downstream logic and CSV export
    expected_cols = [
        "id", "weblink", "category", "level", "player_id",
        "date", "primary_t", "note", "character", "submitted",
        "subcategory_raw"
    ]

    # Normalize API run objects into row dicts with the columns needed
    cleaned_runs = []
    for run in verified_runs:
        player_id = None
        players = run.get("players") or []
        if players:
            player_id = players[0].get("id")

        values = run["values"]
        category_name = category_name_by_id.get(run["category"])
        subcat_cfg = config.subcategories.get(category_name)
        subcategory_raw = values.get(subcat_cfg.var_id) if subcat_cfg else None

        cleaned_runs.append(
            {
                "id": run["id"],
                "weblink": run["weblink"],
                "category": run["category"],
                "level": run.get("level"),
                "player_id": player_id,
                "date": run["date"],
                "primary_t": run["times"]["primary_t"],
                "note": values[config.note_key] if config.note_key else NO_NOTE,
                "character": values[config.character_key] if config.character_key else NO_CHARACTER,
                "submitted": run["submitted"],
                "subcategory_raw": subcategory_raw,
            }
        )

    # Build DataFrame with stable column order
    df = pd.DataFrame(cleaned_runs, columns=expected_cols)

    # Map category/level IDs into readable names
    df["category_name"] = df["category"].map(category_name_by_id)
    df["level_name"] = df["level"].map(level_name_by_id)

    # Map subcategory raw value into its readable name, using the per-category
    # SubcategoryConfig (if the run's category has one)
    def resolve_subcategory_name(row):
        subcat_cfg = config.subcategories.get(row["category_name"])
        if subcat_cfg is None or pd.isna(row["subcategory_raw"]):
            return pd.NA
        return subcat_cfg.value_map.get(row["subcategory_raw"], pd.NA)

    df["subcategory_name"] = df.apply(resolve_subcategory_name, axis=1)

    # Load player cache and lookup for missing display names
    player_cache_file = cache_dir / "players_cache.json"
    player_map = safe_read_json(player_cache_file, default={}) or {}

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

    safe_write_json(player_cache_file, player_map)

    # Convert ID columns to readable columns
    df["player_name"] = df["player_id"].map(player_map)
    df["character_name"] = df["character"].map(config.character_map) if config.character_key else NO_CHARACTER
    df["note_name"] = df["note"].map(config.note_map) if config.note_key else NO_NOTE

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

        # IDs of categories that have subcategories, per the config
        subcat_category_ids = {
            cat["id"] for cat in categories if cat["name"] in config.subcategories
        }
        mask_with_subcat = full_game_df["category"].isin(subcat_category_ids)

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
    df.drop(
        columns=[
            "category", "level", "player_id", "character", "note",
            "subcategory_raw",
        ],
        inplace=True,
    )

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