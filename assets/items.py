import pygame


# ==========================================
# ITEM TEMPLATES & ASSETS REGISTRY
# ==========================================
ITEMS = {
    "crude_sword": {
        "name": "Crude sword",
        "min_atk": 4,
        "max_atk": 8,
        "allowed_classes": ["Warrior", "Ranger"],  # W, R
        "path": "images/crudesword.png",
        "price": 50,
    },
    "longsword": {
        "name": "Longsword",
        "min_atk": 6,
        "max_atk": 10,
        "allowed_classes": ["Warrior", "Ranger"],  # W, R
        "path": "images/longsword.png",
        "price": 120,
    },
    "dagger": {
        "name": "Dagger",
        "min_atk": 2,
        "max_atk": 4,
        "allowed_classes": ["Warrior", "Ranger", "Mage"],  # W, R, M (All)
        "path": "images/dagger.png",
        "price": 40,
    },
    "leather_armor": {
        "name": "Leather Armor",
        "min_def": 2,
        "max_def": 3,
        "allowed_classes": ["Warrior", "Ranger", "Mage"],  # W, R, M (All)
        "path": "images/leather-armor.png",
        "price": 60,
    },
    "scale_armor": {
        "name": "Scale Armor",
        "min_def": 3,
        "max_def": 5,
        "allowed_classes": ["Warrior", "Ranger"],  # W, R
        "path": "images/scale-armor.png",
        "price": 150,
    },
    "bronze_ring": {
        "name": "Bronze Ring",
        "type": "ring",
        "allowed_classes": ["Warrior", "Ranger", "Mage"],  # All classes
        "path": "images/bronzering.png",
        "price": 50,
    },
    "small_shield": {
        "name": "Small shield",
        "type": "shield",
        "min_def": 1,
        "max_def": 2,
        "allowed_classes": ["Warrior"],  # W only
        "path": "images/small-shield.png",
        "price": 40,
    },
}

ITEM_ICONS = {}
_FALLBACK_ICON = None


def get_item(item_id: str) -> dict:
    """Returns a fresh data-only instance copy of an item by its internal ID."""
    if item_id not in ITEMS:
        raise KeyError(f"Unknown item_id: '{item_id}'")

    item = ITEMS[item_id].copy()
    item["id"] = item_id
    return item


def get_item_icon(item: dict) -> pygame.Surface:
    """Returns the preloaded icon surface for an item dict."""
    global _FALLBACK_ICON
    item_id = item.get("id")
    if item_id in ITEM_ICONS:
        return ITEM_ICONS[item_id]

    if _FALLBACK_ICON is None:
        _FALLBACK_ICON = pygame.Surface((34, 34))
        _FALLBACK_ICON.fill((140, 140, 160))
    return _FALLBACK_ICON


def initialize_item_assets():
    """Loads item icon surfaces AFTER pygame.display.set_mode() has been called."""
    for item_id, item_data in ITEMS.items():
        try:
            surf = pygame.image.load(item_data["path"]).convert_alpha()
            ITEM_ICONS[item_id] = pygame.transform.scale(surf, (34, 34))
        except Exception as e:
            print(f"Failed to load '{item_id}' ({item_data['path']}): {e}")
            fallback = pygame.Surface((34, 34))
            fallback.fill((140, 140, 160))
            ITEM_ICONS[item_id] = fallback
