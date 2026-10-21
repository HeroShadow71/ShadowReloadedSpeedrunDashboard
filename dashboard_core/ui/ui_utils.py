"""
UI utilities for option generation, navigation and DataFrame preparation.

Collection of small helpers used by the dashboard UI: sidebar navigation links,
ordered option lists from DataFrame and table/chart formatting utilities.
"""

import pandas as pd


def get_scope_options(config):
    """
    Return the available scope options for a given game.

    "Boss" is only included if the game has boss levels configured.

    :param config: GameConfig instance
    :return: list of scope option strings
    """
    options = ["Individual Level"]
    if config.boss_order:
        options.append("Boss")
    options.append("Full Game")
    return options


def get_level_or_boss_options(df, scope, config):
    """
    Return ordered level or boss names available for the given scope.

    - For "Individual Level" or "Boss", keeps the configured order of
      `config.level_order` or `config.boss_order` and includes only names
      present in the DataFrame.
    - For "Full Game", returns an empty list.

    :param df: source runs DataFrame
    :param scope: one of `"Individual Level"`, `"Boss"` or `"Full Game"`
    :param config: GameConfig instance
    :return: ordered list of level or boss names, or empty list
    """
    if scope in ("Individual Level", "Boss"):
        is_boss = scope == "Boss"
        order = config.boss_order if is_boss else config.level_order
        return [lvl for lvl in order if lvl in df["level_name"].dropna().unique()]
    return []


def get_category_options(df, scope, config, level_name=None):
    """
    Return ordered category options filtered by scope and optional level.

    - For "Individual Level" or "Boss" with a level selected, returns
      categories present in that level.
    - For "Full Game", returns categories from runs without a level.

    :param df: source runs DataFrame
    :param scope: current scope selection
    :param config: GameConfig instance
    :param level_name: optional level name to filter categories for
    :return: ordered list of category names
    """
    if scope in ("Individual Level", "Boss") and level_name:
        return [cat for cat in config.category_order
                if cat in df[df["level_name"] == level_name]["category_name"].unique()]

    return [cat for cat in config.category_order
            if cat in df[df["level_name"].isna()]["category_name"].unique()]


def get_character_note_options(df, config, include_all_chars=False):
    """
    Return ordered character and note option lists.

    - Characters follow `config.character_order` and are limited to those
      present in the DataFrame. Returns `["All"]` (or `[]`) if this game has
      no character variable configured, depending on `include_all_chars`.
    - Notes always start with `"All"` and are sorted alphabetically. Returns
      just `["All"]` if this game has no note variable configured.

    :param df: source runs DataFrame
    :param config: GameConfig instance
    :param include_all_chars: if True, ensure `"All"` is present even with no character variable
    :return: tuple of (`character_options`, `note_options`)
    """
    if config.character_key is None:
        character_options = ["All"] if include_all_chars else []
    else:
        character_options = [
            char for char in config.character_order
            if char in df["character_name"].dropna().unique()
        ]
        if include_all_chars:
            character_options = ["All"] + character_options

    if config.note_key is None:
        note_options = ["All"]
    else:
        note_options = ["All"] + sorted(df["note_name"].dropna().unique())

    return character_options, note_options


def get_subcategory_options(df, category_name, config):
    """
    Return subcategory options for the given category, if configured.

    :param df: source runs DataFrame
    :param category_name: the selected category name
    :param config: GameConfig instance
    :return: ordered list of subcategory names, or empty list if this
        category has no subcategories configured
    """
    subcat_cfg = config.subcategories.get(category_name)
    if subcat_cfg is None:
        return []

    mask = (df["level_name"].isna()) & (df["category_name"] == category_name)
    available_subcategories = set(df.loc[mask, "subcategory_name"].dropna().unique())

    return [sub for sub in subcat_cfg.order if sub in available_subcategories]


def get_player_options(df, scope, level_name=None, category_name=None):
    """
    Return player options filtered by scope, level and category.

    The returned list always begins with the entry `"All Players"`.

    - For `"Full Game"`, returns all players who have runs in the given category.
    - For `"Individual Level"` or `"Boss"`, returns only players who have runs
      for the selected level and category.

    :param df: source runs DataFrame
    :param scope: current scope selection
    :param level_name: optional level name to filter by
    :param category_name: optional category name to filter by
    :return: list of player names with `"All Players"` first
    """
    filtered = df.query("category_name == @category_name")
    if scope in ("Individual Level", "Boss"):
        filtered = filtered.query("level_name == @level_name")

    players = filtered["player_name"].dropna().unique().tolist()

    return ["All Players"] + players if players else ["All Players"]


def prepare_table_df(
    df,
    scope,
    level_name,
    category_name,
    subcategory_name,
    character_selected,
    note_selected,
    show_obsolete,
    format_time_fn
):
    """
    Produce a DataFrame ready for table display.

    Applies selection filters, computes places for display, adds
    formatted time and date columns used for table rendering.

    :param df: source runs DataFrame
    :param scope: scope selection string
    :param level_name: level name when applicable
    :param category_name: category name
    :param subcategory_name: subcategory name (for Story Mode/Unlock Shadow Rifle)
    :param character_selected: selected characters
    :param note_selected: selected note (or `"All"`)
    :param show_obsolete: if True, include obsolete runs
    :param format_time_fn: function that formats numeric times
    :return: `table_df`, a copy of the DataFrame filtered and formatted for table display
    """
    filtered_df = _filter_runs_for_display(
        df, scope, level_name, category_name, subcategory_name, character_selected, note_selected, show_obsolete
    )
    table_df = _format_places_for_display(filtered_df)

    table_df["time_fmt"] = table_df["primary_t"].apply(format_time_fn)
    table_df["date_fmt"] = pd.to_datetime(table_df["date"]).dt.strftime("%d/%m/%Y")

    return table_df


def _filter_runs_for_display(
    df,
    scope,
    level_name,
    category,
    subcategory,
    character_selected,
    note_selected,
    show_obsolete,
):
    """
    Return a filtered DataFrame for display or charting.

    The function returns a filtered view (slice) of the input DataFrame.
    Callers that intend to mutate the result should copy it.

    :param df: source runs DataFrame
    :param scope: scope selection string
    :param level_name: level name when required by scope
    :param category: category name to filter by
    :param subcategory: subcategory name (for Story Mode/Unlock Shadow Rifle)
    :param character_selected: character selection list
    :param note_selected: selected note (or `"All"`)
    :param show_obsolete: include obsolete runs when True
    :return: filtered DataFrame (slice)
    """
    mask = pd.Series(True, index=df.index)

    if not show_obsolete and "obsolete" in df.columns:
        mask &= df["obsolete"] == False

    if scope in ("Individual Level", "Boss"):
        mask &= (df["level_name"] == level_name) & (df["category_name"] == category)
    else:
        mask &= df["category_name"] == category

    if subcategory is not None:
        mask &= df["subcategory_name"] == subcategory

    if character_selected:
        if isinstance(character_selected, str):
            if character_selected != "All":
                mask &= df["character_name"] == character_selected
        else:
            mask &= df["character_name"].isin(character_selected)

    elif character_selected == []:
        return df.iloc[0:0]

    if note_selected != "All":
        mask &= df["note_name"] == note_selected

    return df.loc[mask]


def _format_places_for_display(table_df):
    """
    Add a new integer column `"place_numeric"` used for sorting ranks and
    ensure `"place"` column is a string ready to display both ranking and `Obsolete`.

    :param table_df: DataFrame
    :return: Copy of `table_df`
    """
    table_df = table_df.copy()

    table_df = table_df.sort_values(["primary_t", "date"], na_position="last")

    filter_cols = ("level_name", "category_name", "character_name")
    group_cols = [col for col in filter_cols if col in table_df.columns and table_df[col].notna().any()]

    if not group_cols:
        if "category_name" in table_df.columns and table_df["category_name"].notna().any():
            group_cols = ["category_name"]
        else:
            group_cols = []

    mask_non_obsolete = ~table_df["obsolete"].astype(bool)

    table_df["place_numeric"] = pd.NA

    if mask_non_obsolete.any():
        ranks = (
            table_df.loc[mask_non_obsolete]
            .groupby(group_cols, observed=True)["primary_t"]
            .rank(method="min", ascending=True)
            .astype("Int64")
        )
        table_df.loc[mask_non_obsolete, "place_numeric"] = ranks

    table_df["place"] = table_df["place_numeric"].astype(str)
    table_df.loc[table_df["obsolete"].astype(bool), "place"] = "Obsolete"

    return table_df


def prepare_chart_df(table_df, view_type, player_selection, config):
    """
    Prepare a DataFrame for charting and determine which column defines traces.

    :param table_df: DataFrame containing table view data
    :param view_type: Selected view type (ex: "`PB Progression`")
    :param player_selection: Selected player name or "`All Players`"
    :param config: GameConfig instance
    :return: Tuple (`chart_df, trace_col, pb_char_note_label`)
    """
    chart_df = table_df.copy()

    single_player_chart = (view_type == "PB Progression") and (player_selection != "All Players")
    has_char_or_note = config.character_key is not None or config.note_key is not None

    if single_player_chart:
        chart_df = chart_df[chart_df["player_name"] == player_selection]

    chart_df["note_name"] = chart_df["note_name"].fillna("").astype(str)
    chart_df["character_name"] = chart_df["character_name"].astype(str)

    if single_player_chart and has_char_or_note:
        trace_col = "char_note"
        chart_df[trace_col] = chart_df["character_name"] + " - " + chart_df["note_name"]
        pb_char_note_label = "Character - Note"
    else:
        trace_col = "player_name"
        pb_char_note_label = None

    return chart_df, trace_col, pb_char_note_label
