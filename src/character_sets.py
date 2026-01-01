# character_sets.py
#
# Copyright 2023 Letterpress Contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Character sets for ASCII art generation in different languages."""

# Predefined character sets ordered from darkest/densest to lightest
# The space at the beginning represents the lightest/background character
CHARACTER_SETS = {
    "english": {
        "name": _("English (Default)"),
        "characters": " .:-=+*#%@",
        "description": _("Standard ASCII characters"),
    },
    "characters_art": {
        "name": _("Characters Art"),
        "characters": " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$",
        "description": _("Rich artistic style with varied symbols"),
    },
    "chinese": {
        "name": _("Chinese (中文)"),
        "characters": " 。·：丨丶丿乙亅亠人儿入八冂冖冫几凵刀力勹匕匚匸十卜卩厂厶又",
        "description": _("Simplified Chinese characters"),
    },
    "japanese": {
        "name": _("Japanese (日本語)"),
        "characters": " 。・：｜ノ乙人入八ロ口囗土士夂夊女子宀寸小尢尸屮山巛工己巾干幺",
        "description": _("Japanese Hiragana and Kanji"),
    },
    "arabic": {
        "name": _("Arabic (العربية)"),
        "characters": " ۰·٠ـ،؛ء آ أ ؤ إ ئ ا ب ة ت ث ج ح خ د ذ ر ز س ش ص ض",
        "description": _("Arabic script characters"),
    },
    "hindi": {
        "name": _("Hindi (हिन्दी)"),
        "characters": " ।॰·ऽ॒॑ं ः अ आ इ ई उ ऊ ऋ ए ऐ ओ औ क ख ग घ ङ च छ ज",
        "description": _("Devanagari script"),
    },
    "tamil": {
        "name": _("Tamil (தமிழ்)"),
        "characters": " ௐ॰·ஃ அ ஆ இ ஈ உ ஊ எ ஏ ஐ ஒ ஓ ஔ க ங ச ஞ ட ண த ந ப ம",
        "description": _("Tamil script characters"),
    },
    "emoji": {
        "name": _("Emoji 😊"),
        "characters": " 😀😃😄😁😆😅🤣😂🙂🙃😉😊😇🥰😍🤩😘😗☺️😚😙🥲",
        "description": _("Emoji characters for fun"),
    },
    "blocks": {
        "name": _("Block Elements"),
        "characters": " ░▒▓█",
        "description": _("Unicode block drawing characters"),
    },
}


def get_character_set(name):
    """Get character set by name.
    
    Args:
        name: Name of the character set (e.g., 'english', 'chinese')
        
    Returns:
        Character string for the set, or None if not found
    """
    charset = CHARACTER_SETS.get(name.lower())
    return charset["characters"] if charset else None


def get_all_character_sets():
    """Get all available character sets.
    
    Returns:
        Dictionary of character set names to their data
    """
    return CHARACTER_SETS


def get_character_set_names():
    """Get list of all character set names.
    
    Returns:
        List of character set keys
    """
    return list(CHARACTER_SETS.keys())


def validate_custom_characters(characters):
    """Validate custom character string.
    
    Args:
        characters: Custom character string
        
    Returns:
        True if valid, False otherwise
    """
    if not characters or len(characters) < 2:
        return False
    # Should start with a space (background character)
    if not characters[0].isspace():
        return False
    return True
