"""
GameConfig instance for Shadow Reloaded.
"""

from config.game_config import GameConfig, SubcategoryConfig

CHAR_MAP = {
    "lr36ddwl": "Shadow",
    "1dkonngl": "Gun Android",
    "10v9yypl": "Cannon Android"
}

NOTE_MAP = {
    "qvvz0dwq": "No SG",
    "le2v08zl": "SG"
}

UNLOCK_RIFLE_VAR_MAP = {
    "qj7v6egq": "Any%",
    "q65n9g7l": "Restricted"
}

STORY_MODE_ENDING_MAP = {
    "1dkz06pl": "Planted Memories (147 - NNDNHD)",
    "q8k6y4yq": "Despair's Quickening (243 - HDDHDD)",
    "qyzp0761": "Wandering's End (186 - NNHHNH)",
    "ln8wxeol": "Punishment, Thy Name is Ruin (001 - DDDDDD)",
    "10vz40ol": "A New Empire's Beginning (164 - NNNNNH)",
    "qj703w7q": "A Missive from 50 Years Ago (326 - HHHHHH)",
    "q650dyvl": "Excess of Intellect (041 - DDHHND)",
    "lmok5881": "Coffin of Memories (323 - HHHHND)",
    "1w4pyemq": "The Summit of Power (217 - NHNNHD)",
    "qoxp4m5q": "To Love Oneself (064 - DHNDNH)"
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
    "Dark", "Normal", "Hero", "Expert", "Story Mode", "Expert Mode", "Unlock Shadow Rifle", "100% No Library"
]

STORY_MODE_ENDING_ORDER = [
    "Planted Memories (147 - NNDNHD)",
    "Despair's Quickening (243 - HDDHDD)",
    "Wandering's End (186 - NNHHNH)",
    "Punishment, Thy Name is Ruin (001 - DDDDDD)",
    "A New Empire's Beginning (164 - NNNNNH)",
    "A Missive from 50 Years Ago (326 - HHHHHH)",
    "Excess of Intellect (041 - DDHHND)",
    "Coffin of Memories (323 - HHHHND)",
    "The Summit of Power (217 - NHNNHD)",
    "To Love Oneself (064 - DHNDNH)"
]

UNLOCK_RIFLE_RULESET_ORDER = ["Any%", "Restricted"]

CHARACTER_ORDER = ["Shadow", "Gun Android", "Cannon Android"]

SHADOW_RELOADED = GameConfig(
    key="shadow_reloaded",
    display_name="Shadow Reloaded Speedrun Dashboard",
    game_id="o1y3y346",
    level_order=LEVEL_ORDER,
    boss_order=BOSS_ORDER,
    category_order=CATEGORY_ORDER,
    character_key="38dgox08",
    character_map=CHAR_MAP,
    character_order=CHARACTER_ORDER,
    note_key="68kwme38",
    note_map=NOTE_MAP,
    subcategories={
        "Story Mode": SubcategoryConfig(
            var_id="gnxq5xx8",
            value_map=STORY_MODE_ENDING_MAP,
            order=STORY_MODE_ENDING_ORDER,
            label="Select Ending",
        ),
        "Unlock Shadow Rifle": SubcategoryConfig(
            var_id="wl34pz68",
            value_map=UNLOCK_RIFLE_VAR_MAP,
            order=UNLOCK_RIFLE_RULESET_ORDER,
            label="Select Ruleset",
        ),
    },
)