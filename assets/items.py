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

try:
    sword_surf = pygame.image.load(longsword_item["path"]).convert_alpha()
    longsword_item["icon"] = pygame.transform.scale(sword_surf, (34, 34))
except Exception as e:
    fallback = pygame.Surface((34, 34))
    fallback.fill((140, 140, 160))
    longsword_item["icon"] = fallback

dagger_item = {
    "name": "Dagger",
    "min_atk": 2,
    "max_atk": 4,
    "path": "images/dagger.png",
}

try:
    dagger_surf = pygame.image.load(dagger_item["path"]).convert_alpha()
    dagger_item["icon"] = pygame.transform.scale(dagger_surf, (34, 34))
except Exception as e:
    fallback = pygame.Surface((34, 34))
    fallback.fill((160, 140, 140))
    dagger_item["icon"] = fallback
