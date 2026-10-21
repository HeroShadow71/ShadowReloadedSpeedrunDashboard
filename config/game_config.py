"""
Per-game configuration for the dashboard.

Centralises everything that varies between speedrun.com leaderboards (levels,
categories, variable IDs and subcategory mappings) so the rest of the app can
stay game-agnostic.
"""

from dataclasses import dataclass, field

@dataclass
class SubcategoryConfig:
    """
    Configuration for a full-game category that has subcategories.

    :param var_id: speedrun.com variable ID for this subcategory
    :param value_map: mapping of value ID to readable subcategory name
    :param order: display order for the subcategory options
    :param label: selectbox label shown for this subcategory (ex: "Select Ending")
    """
    var_id: str
    value_map: dict
    order: list
    label: str


@dataclass
class GameConfig:
    """
    Configuration for a single speedrun.com leaderboard/game version.

    :param key: short identifier used for cache file names and the Supabase table
    :param display_name: page title / nav label for this leaderboard
    :param game_id: speedrun.com game ID
    :param level_order: display order for individual levels
    :param boss_order: display order for boss levels; empty if this version has no boss scope
    :param category_order: display order for categories
    :param character_key: speedrun.com variable ID for character, or None if not used
    :param character_map: mapping of character value ID to readable name, or None
    :param character_order: display order for characters, or None
    :param note_key: speedrun.com variable ID for note/SG, or None if not used
    :param note_map: mapping of note value ID to readable name, or None
    :param subcategories: mapping of category name to its SubcategoryConfig
    """
    key: str
    display_name: str
    game_id: str

    level_order: list
    boss_order: list
    category_order: list

    character_key: str = None
    character_map: dict = None
    character_order: list = None

    note_key: str = None
    note_map: dict = None

    subcategories: dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate that character/note fields are set consistently (both or neither)."""
        if (self.character_key is None) != (self.character_map is None):
            raise ValueError(f"{self.key}: character_key and character_map must both be set or both be None")
        if (self.note_key is None) != (self.note_map is None):
            raise ValueError(f"{self.key}: note_key and note_map must both be set or both be None")