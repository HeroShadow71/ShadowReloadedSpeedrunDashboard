"""
Centralised constants and configuration for the dashboard.

This module centralises file paths, API configuration and Plotly settings
that are shared across all games. Game-specific data (levels, categories,
variable mappings) lives in config/<game>.py instead.
"""
from pathlib import Path

# File paths and directories
PROJECT_ROOT = Path.cwd()

DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
PROCESSED_DIR = DATA_DIR / "processed"

STATIC_DIR = PROJECT_ROOT / "static"
IMAGES_DIR = STATIC_DIR / "images"

DASHBOARD_CSS = STATIC_DIR / "dashboard.css"
ABOUT_PAGE_CSS = STATIC_DIR / "about-page.css"

DASHBOARD_FAVICON = IMAGES_DIR / "dashboard-favicon.ico"
ABOUT_PAGE_FAVICON = IMAGES_DIR / "about-page-favicon.ico"

DASHBOARD_LOGO = IMAGES_DIR / "dashboard-logo.png"
STAGE_CHART_PNG = IMAGES_DIR / "stage-chart.png"
SG_SHOWCASE_GIF = IMAGES_DIR / "sg-showcase.gif"

# API configuration
API_PAGE_SIZE = 200
API_TIMEOUT = 10

# Refresh interval (seconds)
COOLDOWN_SECONDS = 1800

VIEW_OPTIONS = [
    "PB Progression",
    "Player Time Improvements",
    "Current WR Counts",
    "Community Overview"
]

# Plotly configuration
CONFIG = {
    "scrollZoom": True,
    "displayModeBar": True,
    "modeBarButtonsToRemove": ["zoomIn2d", "zoomOut2d", "select2d", "lasso2d"]
}