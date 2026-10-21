"""
Shared dashboard page renderer.

Wires data loading, UI controls and view rendering for a given game's
dashboard. Each per-game Streamlit page calls render_dashboard(config)
with its own GameConfig instance.
"""
import logging

import streamlit as st

from constants import DASHBOARD_CSS, DASHBOARD_LOGO
from dashboard_core.data_io import get_data
from dashboard_core.io_utils import ensure_project_dirs
from dashboard_core.utils import format_time_seconds, load_image_as_base64
from dashboard_core.ui.controls import (
    apply_categorical_ordering, render_scope_controls, render_selection_controls
)
from dashboard_core.ui.views import (
    render_table, render_chart,
    plot_pb_progression, plot_time_improvement, plot_wr_count, render_community_overview
)
from dashboard_core.ui.ui_utils import prepare_table_df, prepare_chart_df


def render_dashboard(config):
    """
    Render the full dashboard for a given game.

    Configures the page title, loads the processed runs (from cache or
    remote), and renders the control panel and view selected by the user.

    :param config: GameConfig instance for the game to render
    """
    ensure_project_dirs()

    st.html(DASHBOARD_CSS)

    title_logo = load_image_as_base64(DASHBOARD_LOGO)
    st.html(
    f"""
        <header>
            <img id="title-logo" src='{title_logo}'/>
        </header>
    """
    )

    refresh_btn = st.button("🔄 Refresh Data", key="refresh_btn")
    try:
        if refresh_btn:
            df = get_data(config, force_refresh=True)
        else:
            df = get_data(config, force_refresh=False)
    except Exception:
        logging.exception("Failed to load or process data")
        st.error("Failed to load data. Please try refreshing or check back later.")
        st.stop()

    df = apply_categorical_ordering(df, config)

    with st.expander("Filters and View Options", expanded=True):
        scope = render_scope_controls(config)

        (
            level_name, category_name, subcategory_name,
            view_type, player_selection,
            character_selected, note_selected,
            show_obsolete
        ) = render_selection_controls(df, scope, config)

    table_df = prepare_table_df(
        df,
        scope,
        level_name,
        category_name,
        subcategory_name,
        character_selected,
        note_selected,
        show_obsolete,
        format_time_seconds
    )

    chart_df, trace_col, pb_char_note_label = (
        prepare_chart_df(table_df, view_type, player_selection, config)
    )

    fig = None
    match view_type:
        case "Table":
            render_table(table_df, config)
        case "PB Progression":
            fig = plot_pb_progression(chart_df, trace_col, pb_char_note_label)
        case "Player Time Improvements":
            fig = plot_time_improvement(chart_df)
        case "Current WR Counts":
            fig = plot_wr_count(df, character_selected=character_selected, note_selected=note_selected)
        case "Community Overview":
            render_community_overview(df, config)

    if fig:
        render_chart(fig)