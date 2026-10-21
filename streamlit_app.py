"""
Streamlit app entry point.

Defines the app's pages (one per game dashboard, plus static info pages)
and lets Streamlit's navigation render the sidebar automatically.
"""
import streamlit as st

from constants import DASHBOARD_FAVICON
from config.shadow_reloaded import SHADOW_RELOADED
from config.shadow_sx import SHADOW_SX
from dashboard_core.dashboard_renderer import render_dashboard


def make_dashboard_page(config):
    """
    Build a Streamlit page callable for a given game's dashboard.

    :param config: GameConfig instance
    :return: a zero-argument function suitable for st.Page()
    """
    def page():
        render_dashboard(config)
    return page


st.set_page_config(page_icon=DASHBOARD_FAVICON, layout="wide")

pg = st.navigation({
    "Dashboards": [
        st.Page(
            make_dashboard_page(SHADOW_RELOADED),
            title="Shadow Reloaded",
            icon=":material/bar_chart:",
            default=True,
            url_path=SHADOW_RELOADED.key
        ),
        st.Page(
            make_dashboard_page(SHADOW_SX),
            title="Shadow SX",
            icon=":material/bar_chart:",
            url_path=SHADOW_SX.key
        ),
    ],
    "Info": [
        st.Page(
            "pages/about_page.py", 
            title="Game & Dashboard Info",
            icon=":material/info:"
        ),
    ]
}, position="top")
pg.run()