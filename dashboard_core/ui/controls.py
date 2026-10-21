"""
UI controls and helpers.

Provides rendering helpers for selection controls (scope, level/boss, category)
and small utilities to keep widget layout stable across reruns.
"""
import streamlit as st
import pandas as pd

from constants import VIEW_OPTIONS
from dashboard_core.ui.ui_utils import (
    get_scope_options, get_level_or_boss_options,
    get_category_options, get_character_note_options, get_player_options,
    get_subcategory_options
)


def apply_categorical_ordering(df, config):
    """
    Apply ordered categorical dtype to known columns.

    :param df: runs DataFrame
    :param config: GameConfig instance
    :return: `df` DataFrame with ordered categorical columns applied (in-place)
    """
    for col, order in [
        ("level_name", config.level_order + config.boss_order),
        ("category_name", config.category_order),
        ("character_name", config.character_order or []),
    ]:
        if col in df.columns:
            df[col] = pd.Categorical(df[col], categories=order, ordered=True)

    return df


def render_scope_controls(config):
    """
    Render the scope radio controls.

    Returns the selected scope string, or `None` for views that do not use
    scope selection (overview modes).

    :param config: GameConfig instance
    :return: selected `scope` or `None`
    """
    if st.session_state.get("view_type") in ("Current WR Counts", "Community Overview"):
        return None
    else:
        with st.container(border=True):
            scope = st.radio("Select Scope", get_scope_options(config), horizontal=True, key="scope_radio")
        return scope


def render_selection_controls(df, scope, config):
    """
    Render view and filter widgets and return current selections.

    Builds placeholders and interactive widgets for view, player, character, and
    note selection, along with a checkbox to show obsolete runs. Uses an internal
    helper to maintain stable layout and consistent behavior across reruns.

    :param df: source runs DataFrame used to compute available options
    :param scope: current scope value returned by `render_scope_controls`
    :param config: GameConfig instance
    :return: tuple of:

        - level_name;
        - category_name;
        - subcategory_name;
        - view_type;
        - player_selection;
        - character_selected;
        - note_selected;
        - show_obsolete
    """
    # Quick branch for WR counts, Community Overview
    view_type_current = st.session_state.get("view_type")
    if view_type_current in ("Current WR Counts", "Community Overview"):
        with st.container(border=True):
            is_wr_view = (view_type_current == "Current WR Counts")

            if is_wr_view:
                has_character = config.character_key is not None
                has_note = config.note_key is not None
                n_cols = 1 + has_character + has_note
                cols = st.columns([2] * n_cols)
                col_idx = 0

                view_type = cols[col_idx].selectbox("Select view", ["Table"] + VIEW_OPTIONS, key="view_type")
                col_idx += 1

                if has_character:
                    char_options, _ = get_character_note_options(df, config, include_all_chars=True)
                    character_selected = cols[col_idx].selectbox("Select Character", char_options, key="wr_char_selected")
                    col_idx += 1
                else:
                    character_selected = "All"

                if has_note:
                    _, note_options = get_character_note_options(df, config)
                    note_selected = cols[col_idx].selectbox("Select Note Scope", note_options, key="wr_note_selected")
                else:
                    note_selected = "All"
            else:
                cols = st.columns([2, 3])
                view_type = cols[0].selectbox("Select view", ["Table"] + VIEW_OPTIONS, key="view_type")
                character_selected = "All"
                note_selected = "All"

        return None, None, None, view_type, "All Players", character_selected, note_selected, True

    with st.container(border=True):
        with st.container():
            col1, col2 = st.columns((2, 3))
            with col1:
                lvl_ph = col1.empty()
                if scope in ("Individual Level", "Boss"):
                    level_options = get_level_or_boss_options(df, scope, config)
                    level_name = _render_select_widget(
                        lvl_ph, "Select Level/Boss", level_options, key="level_select"
                    )
                else:
                    level_name = None

            if scope in ("Individual Level", "Boss"):
                with col2:
                    cat_ph = col2.empty()
                    category_options = get_category_options(df, scope, config, level_name=level_name)
                    category_name = _render_select_widget(
                        cat_ph,
                        "Select Category",
                        category_options,
                        key="category_select",
                        auto_select_single=True
                    )
            else:
                with col1:
                    cat_ph = col1.empty()
                    category_options = get_category_options(df, scope, config)
                    category_name = _render_select_widget(
                        cat_ph,
                        "Select Category",
                        category_options,
                        key="category_select",
                        auto_select_single=True
                    )

        subcategory_name = None
        subcategory_options = get_subcategory_options(df, category_name, config) if category_name else []

        if scope == "Full Game" and subcategory_options:
            with st.container():
                subcat_ph = st.empty()
                subcat_cfg = config.subcategories[category_name]
                subcategory_name = _render_select_widget(
                    subcat_ph,
                    subcat_cfg.label,
                    subcategory_options,
                    key="subcategory_select"
                )

        col_char_visual, col_note_visual = st.columns((2, 3))
        char_ph = col_char_visual.empty()
        note_ph = col_note_visual.empty()

    with st.container(border=True):
        col_view_vis, col_player_vis = st.columns([2, 3])
        view_ph = col_view_vis.empty()
        player_ph = col_player_vis.empty()

    view_type = view_ph.selectbox("Select data view", ["Table"] + VIEW_OPTIONS, key="view_type")

    player_selection = "All Players"
    if view_type == "PB Progression" and config.character_key is not None:
        player_options = get_player_options(df, scope, level_name=level_name, category_name=category_name)
        player_selection = _render_select_widget(
            player_ph,
            "Choose a player to view and compare their runs across different characters",
            player_options,
            key="player_selection"
        )
    else:
        player_ph.empty()

    character_options, note_options = get_character_note_options(df, config)

    if category_name == "100% No Library" and config.character_order:
        char_ph.empty()
        character_selected = [config.character_order[0]]

    elif not character_options:
        char_ph.empty()
        character_selected = None
    else:
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

    if len(note_options) > 1:
        note_selected = _render_select_widget(note_ph, "Select Note", note_options, key="note_selected")
    else:
        note_ph.empty()
        note_selected = "All"

    if view_type == "Table":
        show_obsolete = st.checkbox("Show Obsolete Runs", value=False, key="show_obsolete")
    else:
        show_obsolete = True

    return level_name, category_name, subcategory_name, view_type, player_selection, character_selected, note_selected, show_obsolete


def _render_select_widget(
    ph,
    label,
    options,
    key,
    multiselect=False,
    default_all=False,
    always_list=False,
    auto_select_single=False
):
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
    :param auto_select_single: if True and not multiselect, skip rendering when
        there is exactly one option and return it directly
    :return: selected value (string) or list of selected values
    """
    if auto_select_single and not multiselect and len(options) == 1:
        ph.empty()
        val = options[0]
        return [val] if always_list else val

    if not options:
        options = [""]

    if multiselect:
        default = options if default_all else []
        return ph.multiselect(label, options, default=default, key=key)
    else:
        val = ph.selectbox(label, options, key=key)
        return [val] if always_list else val
