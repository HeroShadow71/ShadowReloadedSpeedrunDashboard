"""
UI controls and helpers.

Provides rendering helpers for selection controls (scope, level/boss, category)
and small utilities to keep widget layout stable across reruns.
"""
import streamlit as st
import pandas as pd

from constants import LEVEL_ORDER, BOSS_ORDER, CATEGORY_ORDER, CHARACTER_ORDER, CHART_VIEWS
from dashboard_core.ui.ui_utils import (
    get_scope_options, get_level_or_boss_options,
    get_category_options, get_character_note_options, get_player_options
)


def apply_categorical_ordering(df):
    """
    Apply ordered categorical dtype to known columns.

    :param df: runs DataFrame
    :return: `df` DataFrame with ordered categorical columns applied (in-place)
    """
    for col, order in [
        ("level_name", LEVEL_ORDER + BOSS_ORDER),
        ("category_name", CATEGORY_ORDER),
        ("character_name", CHARACTER_ORDER)
    ]:
        if col in df.columns:
            df[col] = pd.Categorical(df[col], categories=order, ordered=True)
            
    return df


def render_scope_controls():
    """
    Render the scope radio controls.

    Returns the selected scope string, or `None` for views that do not use
    scope selection (overview modes).
    
    :return: selected `scope` or `None`
    """
    if st.session_state.get("view_type") in ("Current WR Counts", "Community Overview"):
        return None
    else:
        with st.container(border=True):
            scope = st.radio("Select Scope", get_scope_options(), horizontal=True, key="scope_radio")
        return scope


def render_selection_controls(df, scope):
    """
    Render view and filter widgets and return current selections.

    Builds placeholders and interactive widgets for view, player, character, and
    note selection, along with a checkbox to show obsolete runs. Uses an internal
    helper to maintain stable layout and consistent behavior across reruns.

    :param df: source runs DataFrame used to compute available options
    :param scope: current scope value returned by `render_scope_controls`
    :return: tuple of: 
    
        - level_name;
        - category_name; 
        - view_type;
        - player_selection;
        - character_selected;
        - note_selected;
        - show_obsolete
    """
    # Quick branch for WR counts, Community Overview
    if st.session_state.get("view_type") in ("Current WR Counts", "Community Overview"):
        with st.container(border=True):
            col_view_vis, _ = st.columns([2, 3])
            view_ph = col_view_vis.empty()
            view_type = view_ph.selectbox("Select view", ["Table"] + CHART_VIEWS, key="view_type")
        return None, None, view_type, "All Players", [], "All", True

    with st.container(border=True):
    # Level/category selectors
        with st.container():
            col1, col2 = st.columns((2, 3))
            # Level/Boss selector
            with col1:
                lvl_ph = col1.empty()
                if scope in ("Individual Level", "Boss"):
                    level_options = get_level_or_boss_options(df, scope)
                    level_name = _render_select_widget(lvl_ph, "Select Level/Boss", level_options, key="level_select")
                else:
                    level_name = None

            # Category selector (filtered by level when applicable)
            if scope in ("Individual Level", "Boss"):
                with col2:
                    cat_ph = col2.empty()
                    category_options = get_category_options(df, scope, level_name=level_name)
                    category_name = _render_select_widget(cat_ph, "Select Category", category_options, key="category_select")
            else:
                with col1:
                    cat_ph = col1.empty()
                    category_options = get_category_options(df, scope)
                    category_name = _render_select_widget(cat_ph, "Select Category", category_options, key="category_select")

        # Reserve placeholders for stable layout
        col_char_visual, col_note_visual = st.columns((2, 3))
        char_ph = col_char_visual.empty()
        note_ph = col_note_visual.empty()

    # Container for view selector and player selector placeholders
    with st.container(border=True):
        col_view_vis, col_player_vis = st.columns([2, 3])
        view_ph = col_view_vis.empty()
        player_ph = col_player_vis.empty()

    # Render the view type selectbox
    view_type = view_ph.selectbox("Select data view", ["Table"] + CHART_VIEWS, key="view_type")

    # Player selection (PB Progression only)
    player_selection = "All Players"
    if view_type == "PB Progression":
        player_options = get_player_options(df, scope, level_name=level_name, category_name=category_name)
        player_selection = _render_select_widget(
            player_ph,
            "Choose a player to view and compare their runs across different characters",
            player_options,
            key="player_selection"
        )
    else:
        player_ph.empty()

    # Character and Note selectors (multiselect only for single-player PB view)
    character_options, note_options = get_character_note_options(df)
    is_char_multi = (view_type == "PB Progression" and player_selection != "All Players")

    character_selected = _render_select_widget(
        char_ph,
        "Select Characters" if is_char_multi else "Select Character",
        character_options,
        key=("character_multi" if is_char_multi else "character_single"),
        multiselect=is_char_multi,
        default_all=True,
        always_list=True,
    )

    # Note selector
    note_selected = _render_select_widget(note_ph, "Select Note", note_options, key="note_selected")

    # "Show Obsolete Runs" checkbox is only shown for the Table view
    if view_type == "Table":
        show_obsolete = st.checkbox("Show Obsolete Runs", value=False, key="show_obsolete")
    else:
        show_obsolete = True

    return level_name, category_name, view_type, player_selection, character_selected, note_selected, show_obsolete


def _render_select_widget(ph, label, options, key, multiselect=False, default_all=False, always_list=False):
    """
    Render a selectbox or multiselect inside a placeholder and return the selection.

    - When `multiselect` is True, returns the list produced by `ph.multiselect`.
      `default_all` will preselect all options for multiselect.
    - When `multiselect` is False, returns a single selected value (string) unless
      `always_list` is True, in which case the single value is wrapped in a list.

    :param ph: Streamlit placeholder container
    :param label: label text for the widget
    :param options: sequence of selectable options
    :param key: Streamlit widget key
    :param multiselect: render a multiselect instead of a selectbox
    :param default_all: if True and multiselect, preselect all options
    :param always_list: if True and not multiselect, wrap single selection in a list
    :return: selected value (string) or list of selected values
    """
    if not options:
        options = [""]

    if multiselect:
        default = options if default_all else []
        return ph.multiselect(label, options, default=default, key=key)
    else:
        val = ph.selectbox(label, options, key=key)
        return [val] if always_list else val
