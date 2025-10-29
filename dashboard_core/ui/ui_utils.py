"""
UI utilities for option generation, navigation and DataFrame preparation.

Collection of small helpers used by the dashboard UI: sidebar navegation links,
ordered option lists from DataFrame and table/chart formatting utilities.
"""
import streamlit as st
import pandas as pd

from constants import (
    APP_FILE, ABOUT_PAGE_FILE,
    LEVEL_ORDER, BOSS_ORDER, CATEGORY_ORDER, CHARACTER_ORDER,
)


def nav_bar():
    """Render the sidebar navigation links.

    Creates page links in the Streamlit sidebar for navigation between
    the main dashboard and the about page.
    """
    with st.sidebar:
        st.page_link(APP_FILE, icon="📊", label="Dashboard")
        st.page_link(ABOUT_PAGE_FILE, label="Game & Dashboard Info")


def get_scope_options():
    """Returns the available scope options."""
    return ["Individual Level", "Boss", "Full Game"]


def get_level_or_boss_options(df, scope):
    """
    Return ordered level or boss names available for the given scope.

    - For "Individual Level" or "Boss", keeps the configured order of
      `LEVEL_ORDER` or `BOSS_ORDER` and includes only names present in the DataFrame.
    - For "Full Game", returns an empty list.

    :param scope: one of `"Individual Level"`, `"Boss"` or `"Full Game"`
    :return: ordered list of level or boss names, or empty list
    """
    if scope in ("Individual Level", "Boss"):
        is_boss = scope == "Boss"
        return [lvl for lvl in (BOSS_ORDER if is_boss else LEVEL_ORDER)
                if lvl in df["level_name"].dropna().unique()]
    return []


def get_category_options(df, scope, level_name=None):
    """
    Return ordered category options filtered by scope and optional level.

    - For "Individual Level" or "Boss" with a level selected, returns
      categories present in that level.
    - For "Full Game", returns categories from runs without a level.
        
    :param scope: current scope selection
    :param level_name: optional level name to filter categories for
    :return: ordered list of category names
    """
    if scope in ("Individual Level", "Boss") and level_name:
            return [cat for cat in CATEGORY_ORDER
                    if cat in df[df["level_name"] == level_name]["category_name"].unique()
            ]

    return [cat for cat in CATEGORY_ORDER 
            if cat in df[df["level_name"].isna()]["category_name"].unique()
    ]
    

def get_character_note_options(df):
    """
    Return ordered character and note option lists.

    - Characters follow the configured CHARACTER_ORDER and are limited to
      those present in the DataFrame.
    - Notes always start with `"All"` and are sorted alphabetically.

    :return: tuple of (`character_options`, `note_options`)
    """
    character_options = [char for char in CHARACTER_ORDER if char in df["character_name"].dropna().unique()]
    note_options = ["All"] + sorted(df["note_name"].dropna().unique())
    return character_options, note_options


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
    :param character_selected: selected characters
    :param note_selected: selected note (or `"All"`)
    :param show_obsolete: if True, include obsolete runs
    :param format_time_fn: function that formats numeric times
    :return: `table_df`, a copy of the DataFrame filtered and formatted for table display
    """
    filtered_df = _filter_runs_for_display(
        df, scope, level_name, category_name, character_selected, note_selected, show_obsolete
    )
    table_df = _format_places_for_display(filtered_df)

    # Add formatted time/date for table display; keep primary_t numeric for charts
    table_df["time_fmt"] = table_df["primary_t"].apply(format_time_fn)
    table_df["date_fmt"] = pd.to_datetime(table_df["date"]).dt.strftime("%d/%m/%Y")

    return table_df


def _filter_runs_for_display(
    df,
    scope,
    level_name,
    category,
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
    :param character_selected: character selection list
    :param note_selected: selected note (or `"All"`)
    :param show_obsolete: include obsolete runs when True
    :return: filtered DataFrame (slice)
    """
    # Use boolean masks to avoid full copies
    mask = pd.Series(True, index=df.index)

    # Exclude obsolete runs unless show_obsolete is True
    if not show_obsolete and "obsolete" in df.columns:
        mask &= df["obsolete"] == False

    # Apply scope-level/category filters
    if scope in ("Individual Level", "Boss"):
        mask &= (df["level_name"] == level_name) & (df["category_name"] == category)
    else:
        mask &= df["category_name"] == category

    # Character filter (empty selection -> empty frame)
    if character_selected:
        mask &= df["character_name"].isin(character_selected)
    else:
        return df.iloc[0:0]

    # Apply note filter unless "All" selected
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

    # Stable sort for display
    table_df = table_df.sort_values(["primary_t", "date"], na_position="last")

    # Initialize columns
    table_df["place_numeric"] = table_df["place"].astype("Int64")

    # Mask non-obsolete rows
    mask_obsolete = table_df["obsolete"].astype(bool)

    # Fill text display
    table_df["place"] = table_df["place_numeric"].astype(str)
    table_df.loc[mask_obsolete, "place"] = "Obsolete"

    return table_df


def prepare_chart_df(table_df, view_type, player_selection):
    """
    Prepare a DataFrame for charting and determine which column defines traces.

    :param table_df: DataFrame containing table view data
    :param view_type: Selected view type (ex: "`PB Progression`")
    :param player_selection: Selected player name or "`All Players`"
    :return: Tuple (`chart_df, trace_col, pb_char_note_label`) where:
    
        - chart_df - copy of `table_df` with "`character_name`" and "`note_name`" coerced to strings
        (adds "char_note" for single-player PB progression)
        - trace_col - column name used for traces ("`char_note`" or "`player_name`")
        - pb_char_note_label - "`Character - Note`" when applicable, else `None`
    """ 
    chart_df = table_df.copy()
    
    # Define whether this is a single-player chart case
    single_player_chart = (view_type == "PB Progression") and (player_selection != "All Players")
    
    # Filter only the selected player's runs if applicable
    if single_player_chart:
        chart_df = chart_df[chart_df["player_name"] == player_selection]

    chart_df["note_name"] = chart_df["note_name"].fillna("").astype(str)
    chart_df["character_name"] = chart_df["character_name"].astype(str)
    
    # Single-player PB Progression uses character+note traces
    if single_player_chart:
        trace_col = "char_note"
        chart_df[trace_col] = chart_df["character_name"] + " - " + chart_df["note_name"]
        pb_char_note_label = "Character - Note"
    else:
        trace_col = "player_name"
        pb_char_note_label = None

    return chart_df, trace_col, pb_char_note_label
