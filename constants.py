"""
Centralised constants and configuration for the dashboard.

This module centralises file paths, API configuration, fixed mappings and
ordering lists used by the dashboard. Keep this file small and declarative
so it is safe to import from many places in the application.
"""
from pathlib import Path

# File paths and directories
PROJECT_ROOT = Path.cwd()
APP_FILE = PROJECT_ROOT / "streamlit_app.py"

DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
PROCESSED_DIR = DATA_DIR / "processed"

CACHE_FILE = CACHE_DIR / "shadow_reloaded_runs_cache.json"
PLAYER_CACHE_FILE = CACHE_DIR / "shadow_reloaded_players_cache.json"
CATEGORY_CACHE_FILE = CACHE_DIR / "shadow_reloaded_categories_cache.json"
LEVEL_CACHE_FILE = CACHE_DIR / "shadow_reloaded_levels_cache.json"
LAST_REFRESH_FILE = CACHE_DIR / "last_refresh.json"

DATA_FILE = PROCESSED_DIR / "shadow_reloaded_runs_processed.csv"

PAGES_DIR = PROJECT_ROOT / "pages"
ABOUT_PAGE_FILE = PAGES_DIR / "about_page.py"

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
GAME_ID = "o1y3y346"
API_PAGE_SIZE = 200
API_TIMEOUT = 10

# Refresh interval (seconds)
COOLDOWN_SECONDS = 7200

# Speedrun.com variable IDs used by the app
NOTE_KEY = "68kwme38"
CHARACTER_KEY = "38dgox08"

# Manual mappings and ordering used by selection controls
CHAR_MAP = {
    "lr36ddwl": "Shadow",
    "1dkonngl": "Gun Android",
    "10v9yypl": "Cannon Android"
}

NOTE_MAP = {
    "qvvz0dwq": "No SG",
    "le2v08zl": "SG"
}

LEVEL_ORDER = [
    "Westopolis", "Digital Circuit", "Glyphic Canyon", "Lethal Highway", "Cryptic Castle",
    "Prison Island", "Circus Park", "Central City", "The Doom", "Sky Troops",
    "Mad Matrix", "Death Ruins", "The ARK", "Air Fleet", "Iron Jungle",
    "Space Gadget", "Lost Impact", "GUN Fortress", "Black Comet", "Lava Shelter",
    "Cosmic Fall", "Final Haunt", "The Last Way"
]

BOSS_ORDER = [
    "Black Bull (Lethal Highway)", "Egg Breaker (Cryptic Castle)", "Heavy Dog", "Egg Breaker (Mad Matrix)",
    "Black Bull (Death Ruins)", "Blue Falcon", "Egg Breaker (Iron Jungle)", "Diablon (GUN Fortress)",
    "Black Doom (GUN Fortress)", "Diablon (Black Comet)", "Egg Dealer (Black Comet)", "Egg Dealer (Lava Shelter)",
    "Egg Dealer (Cosmic Fall)", "Black Doom (Cosmic Fall)", "Diablon (Final Haunt)", "Black Doom (Final Haunt)",
    "Devil Doom"
]

CATEGORY_ORDER = [
    "Dark", "Normal", "Hero", "Expert", "Planted Memories (147)", "Despair's Quickening (243)", "Wandering's End (186)",
    "Punishment, Thy Name is Ruin (001)", "A New Empire's Beginning (164)", "A Missive from 50 Years Ago (326)",
    "Excess of Intellect (041)", "Coffin of Memories (323)", "The Summit of Power (217)", "To Love Oneself (064)",
    "Expert Mode"
]

CHARACTER_ORDER = ["Shadow", "Gun Android", "Cannon Android"]

CHART_VIEWS = [
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
