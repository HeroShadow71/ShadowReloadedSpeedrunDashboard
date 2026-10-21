"""
GameConfig instance for Shadow the Hedgehog SX.
"""

from config.game_config import GameConfig, SubcategoryConfig

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
    "Dark", "Normal", "Hero", "Expert", "Story Mode", "Expert Mode", "All Endings", "100% No Library"
]

ENDING_MAP = {
    "14ogdpjq": "Punishment, Thy Name is Ruin (001 - DDDDDD)",
    "qyzojyd1": "One to Succeed a God (144 - NNDNDH)",
    "le2z85zl": "Planted Memories (147 - NNDNHD)",
    "lx5o49r1": "A New Empire's Beginning (164 - NNNNNH)",
    "1w4okk6q": "Wandering's End (186 - NNHHNH)",
    "q5vz8pnl": "A Use for a Saved Life (322 - HHHDHH)",
    "192yrkkq": "A Missive from 50 Years Ago (326 - HHHHHH)",
}

ENDING_ORDER = [
    "Punishment, Thy Name is Ruin (001 - DDDDDD)",
    "One to Succeed a God (144 - NNDNDH)",
    "Planted Memories (147 - NNDNHD)",
    "A New Empire's Beginning (164 - NNNNNH)",
    "Wandering's End (186 - NNHHNH)",
    "A Use for a Saved Life (322 - HHHDHH)",
    "A Missive from 50 Years Ago (326 - HHHHHH)",
]

SHADOW_SX = GameConfig(
    key="shadow_sx",
    display_name="Shadow SX Speedrun Dashboard",
    game_id="yd4rwmp1",
    level_order=LEVEL_ORDER,
    boss_order=BOSS_ORDER,
    category_order=CATEGORY_ORDER,
    subcategories={
        "Story Mode": SubcategoryConfig(
            var_id="rn1kwvvl",
            value_map=ENDING_MAP,
            order=ENDING_ORDER,
            label="Select Ending",
        ),
    },
)