import pygame

# ==========================================
# ITEM DEFINITIONS & ASSETS
# ==========================================
longsword_item = {
    "name": "Longsword",
    "min_atk": 4,
    "max_atk": 8,
    "path": "images/longsword.png",
}

dagger_item = {
    "name": "Dagger",
    "min_atk": 2,
    "max_atk": 4,
    "path": "images/dagger.png",
}

leather_armor_item = {
    "name": "Leather Armor",
    "min_def": 2,
    "max_def": 3,
    "path": "images/leather-armor.png",
}

scale_armor_item = {
    "name": "Scale Armor",
    "min_def": 3,
    "max_def": 5,
    "path": "images/scale-armor.png",
}


def initialize_item_assets():
    """Loads item icons after Pygame display mode has been initialized."""
    items = [longsword_item, dagger_item, leather_armor_item, scale_armor_item]
    for item in items:
        try:
            surf = pygame.image.load(item["path"]).convert_alpha()
            item["icon"] = pygame.transform.scale(surf, (34, 34))
        except Exception as e:
            fallback = pygame.Surface((34, 34))
            fallback.fill((140, 140, 160))
            item["icon"] = fallback
