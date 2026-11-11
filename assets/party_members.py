import pygame
from assets.items import dagger_item, longsword_item, leather_armor_item, scale_armor_item

party_members = [
    {
        "name": "Thorne",
        "class": "Warrior",
        "path": "images/male-warrior.jpg",
        "level": 1,
        "exp": 0,
        "hp_per_level": 10,
        "mp_per_level": 0,
        "hp": 10,
        "max_hp": 10,
        "mp": 0,
        "max_mp": 0,
        "weapon": longsword_item,
        "armor": scale_armor_item,
        "spells": [],
    },
    {
        "name": "Lyra",
        "class": "Mage",
        "path": "images/female-mage.jpg",
        "level": 1,
        "exp": 0,
        "hp_per_level": 5,
        "mp_per_level": 10,
        "hp": 5,
        "max_hp": 5,
        "mp": 10,
        "max_mp": 10,
        "weapon": dagger_item,
        "armor": leather_armor_item,
        "spells": ["Magic Arrow", "Heal"],
    },
    {
        "name": "Reece",
        "class": "Warrior",
        "path": "images/male-warrior-2.jpg",
        "level": 1,
        "exp": 0,
        "hp_per_level": 10,
        "mp_per_level": 0,
        "hp": 10,
        "max_hp": 10,
        "mp": 0,
        "max_mp": 0,
        "weapon": longsword_item,
        "armor": scale_armor_item,
        "spells": [],
    },
    {
        "name": "Vesper",
        "class": "Ranger",
        "path": "images/female-ranger.jpg",
        "level": 1,
        "exp": 0,
        "hp_per_level": 8,
        "mp_per_level": 3,
        "hp": 8,
        "max_hp": 8,
        "mp": 3,
        "max_mp": 3,
        "weapon": longsword_item,
        "armor": scale_armor_item,
        "spells": ["Magic Arrow", "Heal"],
    },
]

HERO_PORTRAIT_SIZE = 96


def initialize_hero_avatars():
    for hero in party_members:
        hero["heal_flash"] = 0
        # Calculate stats based on level
        hero["max_hp"] = hero["level"] * hero["hp_per_level"]
        hero["max_mp"] = hero["level"] * hero["mp_per_level"]
        hero["hp"] = min(hero["hp"], hero["max_hp"])
        hero["mp"] = min(hero["mp"], hero["max_mp"])

        try:
            surf = pygame.image.load(hero["path"]).convert_alpha()
            hero["avatar"] = pygame.transform.scale(surf, (HERO_PORTRAIT_SIZE, HERO_PORTRAIT_SIZE))
        except Exception as e:
            fallback = pygame.Surface((HERO_PORTRAIT_SIZE, HERO_PORTRAIT_SIZE))
            fallback.fill((100, 100, 120))
            hero["avatar"] = fallback
