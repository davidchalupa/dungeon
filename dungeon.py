import math
import random
import sys
import pygame

import numpy as np
from engine.floor import FloorCaster, surface_to_array, make_sky, build_floor_luts, draw_sun

from engine.textures import FLOOR_TEXTURES

from assets.items import initialize_item_assets, dagger_item, longsword_item
from assets.levels import LEVELS
from assets.party_members import party_members
from assets.spells import SPELLS
import engine.combat as combat
import engine.renderer as renderer
from engine.procedural_sprites import get_cached_procedural_goblin_ghost

# Initialize Pygame
pygame.init()

# Virtual Logical Resolution (Maintains pristine UI and raycaster layout)
VIRTUAL_WIDTH, VIRTUAL_HEIGHT = 840, 740
RENDER_WIDTH, RENDER_HEIGHT = 840, 546

# Get desktop display info for responsive sizing and full-screen switching
info = pygame.display.Info()
DESKTOP_WIDTH = info.current_w
DESKTOP_HEIGHT = info.current_h

# Initial window size maintaining the exact 840x740 aspect ratio
INIT_HEIGHT = min(740, int(DESKTOP_HEIGHT * 0.8))
INIT_WIDTH = int(INIT_HEIGHT * (VIRTUAL_WIDTH / VIRTUAL_HEIGHT))

is_fullscreen = False

# Set up resizable display window
window = pygame.display.set_mode((INIT_WIDTH, INIT_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Dungeon Engine - High Speed & Bright")

# Optimized 3D Rendering Surface
screen = pygame.Surface((RENDER_WIDTH, RENDER_HEIGHT))

# Virtual Master Surface for entire UI & Game View
game_surface = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))

clock = pygame.time.Clock()

# Load Fonts for UI
font_med = pygame.font.SysFont(None, 20)
font_large = pygame.font.SysFont(None, 24)
font_title = pygame.font.SysFont(None, 28, bold=True)

HERO_PORTRAIT_SIZE = 96


# Wrap asset loading in a function to prevent parser freeze on open
def initialize_hero_avatars():
    for hero in party_members:
        hero["heal_flash"] = 0
        try:
            surf = pygame.image.load(hero["path"]).convert_alpha()
            hero["avatar"] = pygame.transform.scale(surf, (HERO_PORTRAIT_SIZE, HERO_PORTRAIT_SIZE))
        except Exception as e:
            fallback = pygame.Surface((HERO_PORTRAIT_SIZE, HERO_PORTRAIT_SIZE))
            fallback.fill((100, 100, 120))
            hero["avatar"] = fallback


initialize_hero_avatars()
initialize_item_assets()

floor_caster = FloorCaster(RENDER_WIDTH, RENDER_HEIGHT)
sky_surface = make_sky(RENDER_WIDTH, RENDER_HEIGHT // 2 + 1)

def _to_frames(entry):
    return entry if isinstance(entry, list) else [entry]

FLOOR_ARRAYS = {
    tid: [surface_to_array(f) for f in _to_frames(entry)]
    for tid, entry in FLOOR_TEXTURES.items()
}

floor_map_array = None   # numpy copy of WORLD_MAP, rebuilt per level
floor_tex_arrays = {}    # cell value -> list of frame arrays

current_level_id = 1
level_data = LEVELS[current_level_id]
WORLD_MAP = level_data["map"]
combat.WORLD_MAP = WORLD_MAP  # Sync map with combat module
active_texture_id = level_data["texture_id"]
opponents = [dict(o) for o in level_data["opponents"]]

posX, posY = 1.5, 1.5
dirX, dirY = -1.0, 0.0
planeX, planeY = 0.0, 0.4

MOVE_SPEED = 0.04
ROT_SPEED = 0.035
PLAYER_RADIUS = 0.22

CEILING_COLOR = (40, 40, 50)
FLOOR_COLOR = (60, 50, 40)

selected_hero_index = 0
viewing_character = None
viewing_spell_book = None
targeting_spell = None
spellcaster = None
in_combat = False
current_opponent = None
combat_message = "Exploring the dungeon..."
attack_flash_timer = 0
spell_effect_timer = 0

floor_kind_lut = None
floor_luts = []


def load_level(level_id):
    global current_level_id, level_data, WORLD_MAP
    global active_texture_id, posX, posY
    global dirX, dirY, planeX, planeY, opponents, in_combat, current_opponent, combat_message
    global floor_map_array, floor_tex_arrays
    global floor_kind_lut, floor_luts

    current_level_id = level_id
    level_data = LEVELS[level_id]
    WORLD_MAP = level_data["map"]
    combat.WORLD_MAP = WORLD_MAP  # Keep combat module synced
    active_texture_id = level_data["texture_id"]

    posX, posY = 1.5, 1.5
    dirX, dirY = -1.0, 0.0
    planeX, planeY = 0.0, 0.4

    opponents = [dict(o) for o in level_data["opponents"]]
    in_combat = False
    current_opponent = None
    combat_message = "Exploring the dungeon..."

    floor_map_array = np.array(WORLD_MAP)
    floor_tex_arrays = {}
    fid = level_data.get("floor_texture_id")
    if fid:
        floor_tex_arrays[0] = FLOOR_ARRAYS[fid]
    if any(2 in row for row in WORLD_MAP):
        floor_tex_arrays[2] = FLOOR_ARRAYS[2]

    if floor_tex_arrays:
        floor_kind_lut, floor_luts = build_floor_luts(np.array(WORLD_MAP), floor_tex_arrays)
    else:
        floor_kind_lut, floor_luts = None, []


# ==========================================
# PARTY UI RENDER (Seamless Bottom Bar)
# ==========================================
def draw_party_ui(surface, current_actor=None, targeting_active=False):
    w = surface.get_width()
    ui_top = 546
    ui_height = VIRTUAL_HEIGHT - ui_top  # 194px seamlessly fills the bottom
    bar_rect = pygame.Rect(0, ui_top, w, ui_height)
    pygame.draw.rect(surface, (20, 20, 25), bar_rect)
    pygame.draw.line(surface, (50, 50, 60), (0, ui_top), (w, ui_top), 2)

    spacing = 160
    start_x = (w - (len(party_members) * spacing)) / 2

    total_content_height = HERO_PORTRAIT_SIZE + 6 + 16 + 6 + 5 + 4 + 5
    start_y = ui_top + (ui_height - total_content_height) // 2 + 6
    portrait_offset = (spacing - HERO_PORTRAIT_SIZE) // 2

    for i, hero in enumerate(party_members):
        slot_x = start_x + i * spacing
        cx = slot_x + portrait_offset

        surface.blit(hero["avatar"], (cx, start_y))

        # Healing flash effect
        if hero.get("heal_flash", 0) > 0:
            flash_surf = pygame.Surface((HERO_PORTRAIT_SIZE, HERO_PORTRAIT_SIZE), pygame.SRCALPHA)
            alpha = int(140 * (hero["heal_flash"] / 30))
            flash_surf.fill((60, 255, 120, alpha))
            surface.blit(flash_surf, (cx, start_y))
            pygame.draw.rect(surface, (100, 255, 150), (cx, start_y, HERO_PORTRAIT_SIZE, HERO_PORTRAIT_SIZE), 3)

        # Targeting mode highlight (bright pulsing border & number badge)
        if targeting_active:
            pulse = int(abs(math.sin(pygame.time.get_ticks() * 0.01)) * 100) + 155
            pygame.draw.rect(surface, (pulse, 255, pulse),
                             (cx - 4, start_y - 4, HERO_PORTRAIT_SIZE + 8, HERO_PORTRAIT_SIZE + 8), 4)

            # Badge overlay
            badge_rect = pygame.Rect(cx + HERO_PORTRAIT_SIZE - 28, start_y + 4, 24, 24)
            pygame.draw.rect(surface, (20, 160, 60), badge_rect)
            pygame.draw.rect(surface, (255, 255, 255), badge_rect, 2)
            badge_txt = font_large.render(str(i + 1), True, (255, 255, 255))
            surface.blit(badge_txt, badge_txt.get_rect(center=badge_rect.center))
        elif current_actor == hero:
            pygame.draw.rect(
                surface, (255, 215, 0), (cx - 3, start_y - 3, HERO_PORTRAIT_SIZE + 6, HERO_PORTRAIT_SIZE + 6), 3
            )

        name_y = start_y + HERO_PORTRAIT_SIZE + 6
        name_txt = font_med.render(
            f"[{i + 1}] {hero['name']}",
            True,
            (230, 230, 230) if hero["hp"] > 0 else (120, 120, 120),
        )
        name_rect = name_txt.get_rect(midtop=(slot_x + spacing / 2, name_y))
        surface.blit(name_txt, name_rect)

        hp_bar_width = HERO_PORTRAIT_SIZE - 10
        hp_bar_height = 5
        hp_bar_x = cx + 5
        hp_bar_y = name_y + 16 + 6

        bg_bar_rect = pygame.Rect(hp_bar_x, hp_bar_y, hp_bar_width, hp_bar_height)
        pygame.draw.rect(surface, (60, 30, 30), bg_bar_rect)

        hp_ratio = max(0.0, min(1.0, hero["hp"] / max(1, hero["max_hp"])))
        fill_width = int(hp_bar_width * hp_ratio)
        if fill_width > 0:
            fill_bar_rect = pygame.Rect(hp_bar_x, hp_bar_y, fill_width, hp_bar_height)
            bar_color = (50, 205, 50) if hero["hp"] > 0 else (150, 150, 150)
            pygame.draw.rect(surface, bar_color, fill_bar_rect)
        pygame.draw.rect(surface, (100, 100, 100), bg_bar_rect, 1)

        # MP Bar
        if hero.get("max_mp", 0) > 0:
            mp_bar_y = hp_bar_y + hp_bar_height + 4
            bg_mp_rect = pygame.Rect(hp_bar_x, mp_bar_y, hp_bar_width, hp_bar_height)
            pygame.draw.rect(surface, (30, 30, 60), bg_mp_rect)
            mp_ratio = max(0.0, min(1.0, hero["mp"] / max(1, hero["max_mp"])))
            mp_fill_width = int(hp_bar_width * mp_ratio)
            if mp_fill_width > 0:
                mp_fill_rect = pygame.Rect(hp_bar_x, mp_bar_y, mp_fill_width, hp_bar_height)
                pygame.draw.rect(surface, (70, 150, 255), mp_fill_rect)
            pygame.draw.rect(surface, (80, 80, 120), bg_mp_rect, 1)


# ==========================================
# SPELL BOOK SUBSCREEN RENDER
# ==========================================
def draw_spell_book(surface, hero):
    w = surface.get_width()
    bg_rect = pygame.Rect(0, 0, w, 580)
    pygame.draw.rect(surface, (20, 20, 35), bg_rect)
    pygame.draw.rect(surface, (100, 140, 220), bg_rect, 3)

    title_txt = font_large.render(
        f"Spell Book: {hero['name']} ({hero['class']}) — Mana: {hero['mp']} / {hero['max_mp']}",
        True,
        (160, 210, 255),
    )
    surface.blit(title_txt, (bg_rect.x + 20, bg_rect.y + 15))
    pygame.draw.line(
        surface,
        (60, 80, 120),
        (bg_rect.x + 20, bg_rect.y + 45),
        (bg_rect.right - 20, bg_rect.y + 45),
        1,
    )

    spells = hero.get("spells", [])
    if not spells:
        no_spell_txt = font_large.render("No spells learned.", True, (170, 170, 170))
        surface.blit(no_spell_txt, (bg_rect.x + 25, bg_rect.y + 75))
    else:
        for i, s_name in enumerate(spells):
            spell = SPELLS[s_name]
            sy = bg_rect.y + 75 + i * 85

            spell_box = pygame.Rect(bg_rect.x + 25, sy, bg_rect.width - 50, 70)
            pygame.draw.rect(surface, (30, 30, 48), spell_box)
            pygame.draw.rect(surface, (80, 120, 180), spell_box, 2)

            icon_rect = pygame.Rect(spell_box.x + 12, spell_box.y + 12, 46, 46)
            pygame.draw.rect(surface, (40, 70, 130), icon_rect)
            if s_name == "Magic Arrow":
                pygame.draw.line(surface, (200, 240, 255), (icon_rect.left + 10, icon_rect.centery),
                                 (icon_rect.right - 10, icon_rect.centery), 3)
                pygame.draw.line(surface, (200, 240, 255), (icon_rect.right - 16, icon_rect.centery - 8),
                                 (icon_rect.right - 10, icon_rect.centery), 3)
                pygame.draw.line(surface, (200, 240, 255), (icon_rect.right - 16, icon_rect.centery + 8),
                                 (icon_rect.right - 10, icon_rect.centery), 3)
            elif s_name == "Heal":
                # Draw clear red medical/pharmacy cross for Heal spell
                pygame.draw.rect(surface, (40, 70, 130), icon_rect)

                center_x = icon_rect.centerx
                center_y = icon_rect.centery

                # A subtle glow effect
                pygame.draw.line(surface, (255, 180, 180),
                                 (center_x - 15, center_y + 1),
                                 (center_x + 17, center_y + 1), width=2)
                pygame.draw.line(surface, (255, 180, 180),
                                 (center_x + 1, center_y - 15),
                                 (center_x + 1, center_y + 17), width=3)
                # Vertical bar - extends up/down from center
                pygame.draw.line(surface, (255, 80, 80),
                                 (center_x, center_y - 16),
                                 (center_x, center_y + 16), width=3)
                # Horizontal bar - extends left/right from center
                pygame.draw.line(surface, (255, 80, 80),
                                 (center_x - 16, center_y),
                                 (center_x + 16, center_y), width=3)

            name_txt = font_large.render(f"[{i + 1}] {spell['name']}", True, (255, 255, 255))
            cost_txt = font_med.render(f"Cost: {spell['cost']} MP", True, (120, 180, 255))

            if "damage" in spell:
                stat_str = f"Damage: {spell['damage']}"
            elif "healing" in spell:
                stat_str = f"Heal: {spell['healing']}"
            else:
                stat_str = ""

            dmg_txt = font_med.render(stat_str, True, (255, 120, 120))
            desc_txt = font_med.render(spell['desc'], True, (180, 180, 190))

            surface.blit(name_txt, (spell_box.x + 75, spell_box.y + 12))
            surface.blit(cost_txt, (spell_box.x + 280, spell_box.y + 14))
            surface.blit(dmg_txt, (spell_box.x + 400, spell_box.y + 14))
            surface.blit(desc_txt, (spell_box.x + 75, spell_box.y + 38))

    footer_txt = font_med.render(
        "Press [1-2] to Select Spell  |  [ESC] Return", True, (170, 170, 170)
    )
    surface.blit(footer_txt, footer_txt.get_rect(center=(bg_rect.centerx, 520)))


# ==========================================
# CHARACTER SUBSCREEN RENDER
# ==========================================
def draw_character_subscreen(surface, hero):
    w = surface.get_width()
    bg_rect = pygame.Rect(0, 0, w, 580)
    pygame.draw.rect(surface, (22, 22, 28), bg_rect)
    pygame.draw.rect(surface, (160, 140, 90), bg_rect, 3)

    title_txt = font_large.render(
        f"Character Sheet: {hero['name']} ({hero['class']})",
        True,
        (240, 220, 150),
    )
    surface.blit(title_txt, (bg_rect.x + 20, bg_rect.y + 15))
    pygame.draw.line(
        surface,
        (90, 80, 55),
        (bg_rect.x + 20, bg_rect.y + 45),
        (bg_rect.right - 20, bg_rect.y + 45),
        1,
    )

    avatar_x = bg_rect.x + 25
    avatar_y = bg_rect.y + 60
    surface.blit(hero["avatar"], (avatar_x, avatar_y))

    stats_x = avatar_x + 110
    stats_y = avatar_y + 5
    name_txt = font_large.render(hero["name"], True, (255, 255, 255))
    class_txt = font_med.render(f"Class: {hero['class']}", True, (180, 180, 190))
    hp_txt = font_med.render(
        f"Hit Points: {hero['hp']} / {hero['max_hp']}", True, (120, 220, 120)
    )
    mp_txt = font_med.render(
        f"Mana: {hero['mp']} / {hero['max_mp']}", True, (120, 180, 255)
    )

    if hero["weapon"] is not None:
        atk_str = f"Attack: {hero['weapon']['min_atk']}-{hero['weapon']['max_atk']}"
    else:
        atk_str = "Attack: 0"
    atk_txt = font_med.render(atk_str, True, (220, 120, 120))

    surface.blit(name_txt, (stats_x, stats_y))
    surface.blit(class_txt, (stats_x, stats_y + 25))
    surface.blit(hp_txt, (stats_x, stats_y + 50))
    surface.blit(mp_txt, (stats_x, stats_y + 75))
    surface.blit(atk_txt, (stats_x, stats_y + 100))

    sil_center_x = bg_rect.centerx
    sil_center_y = bg_rect.centery + 30
    sil_color = (55, 55, 70)

    pygame.draw.circle(surface, sil_color, (sil_center_x, sil_center_y - 80), 20)
    torso_rect = pygame.Rect(sil_center_x - 28, sil_center_y - 55, 56, 85)
    pygame.draw.rect(surface, sil_color, torso_rect, border_radius=6)
    pygame.draw.rect(
        surface,
        sil_color,
        (sil_center_x - 46, sil_center_y - 50, 14, 75),
        border_radius=4,
    )
    pygame.draw.rect(
        surface,
        sil_color,
        (sil_center_x + 32, sil_center_y - 50, 14, 75),
        border_radius=4,
    )

    armor_slot_rect = pygame.Rect(sil_center_x - 20, sil_center_y - 40, 40, 40)
    pygame.draw.rect(surface, (30, 30, 38), armor_slot_rect)
    pygame.draw.rect(surface, (110, 100, 70), armor_slot_rect, 2)

    weapon_slot_rect = pygame.Rect(sil_center_x - 80, sil_center_y - 20, 40, 40)
    pygame.draw.rect(surface, (30, 30, 38), weapon_slot_rect)
    pygame.draw.rect(surface, (110, 100, 70), weapon_slot_rect, 2)

    if hero["weapon"] is not None and "icon" in hero["weapon"]:
        icon_rect = hero["weapon"]["icon"].get_rect(center=weapon_slot_rect.center)
        surface.blit(hero["weapon"]["icon"], icon_rect)

    footer_txt = font_med.render(
        "Press [ESC] to return to Dungeon", True, (170, 170, 170)
    )
    surface.blit(footer_txt, footer_txt.get_rect(center=(bg_rect.centerx, 390)))


# Helper function to select and cast spell
def select_spell_from_book(hero, spell_idx):
    global viewing_spell_book, targeting_spell, spellcaster, in_combat, current_opponent, combat_message, spell_effect_timer
    spells = hero.get("spells", [])
    if len(spells) > spell_idx:
        s_name = spells[spell_idx]
        spell = SPELLS[s_name]

        if hero["mp"] >= spell["cost"]:
            if s_name == "Magic Arrow":
                if in_combat and current_opponent and current_opponent["alive"]:
                    hero["mp"] -= spell["cost"]
                    dmg = spell["damage"]
                    current_opponent["hp"] = max(0, current_opponent["hp"] - dmg)
                    spell_effect_timer = 25

                    if current_opponent["hp"] <= 0:
                        current_opponent["alive"] = False
                        combat_message = f"Victory! {hero['name']} casts {s_name} and obliterates the {current_opponent['name']}!"
                        in_combat = False
                        current_opponent = None
                    else:
                        combat_message = f"{hero['name']} casts {s_name} for {dmg} magical damage! Next turn..."
                        combat.turn_index += 1
                    viewing_spell_book = None
                else:
                    combat_message = "Magic Arrow can only be cast in combat!"
                    viewing_spell_book = None
            elif s_name == "Heal":
                viewing_spell_book = None
                targeting_spell = "Heal"
                spellcaster = hero
                combat_message = f"CHOOSE PARTY MEMBER TO HEAL: Press [1-4]"
        else:
            combat_message = f"Not enough mana to cast {s_name}!"
            viewing_spell_book = None


# ==========================================
# MAIN GAME LOOP
# ==========================================
running = True
while running:
    # Update heal flash animation timers
    for hero in party_members:
        if hero.get("heal_flash", 0) > 0:
            hero["heal_flash"] -= 1

    current_actor = None
    if in_combat and combat.turn_queue and combat.turn_index < len(combat.turn_queue):
        current_actor = combat.turn_queue[combat.turn_index]
    else:
        current_actor = party_members[selected_hero_index]

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                is_fullscreen = not is_fullscreen
                if is_fullscreen:
                    window = pygame.display.set_mode((DESKTOP_WIDTH, DESKTOP_HEIGHT), pygame.FULLSCREEN)
                else:
                    window = pygame.display.set_mode((INIT_WIDTH, INIT_HEIGHT), pygame.RESIZABLE)
            elif targeting_spell is not None:
                if event.key == pygame.K_ESCAPE:
                    targeting_spell = None
                    spellcaster = None
                    combat_message = "Spell targeting cancelled."
                elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                    target_idx = event.key - pygame.K_1
                    if target_idx < len(party_members):
                        target_hero = party_members[target_idx]
                        spell = SPELLS[targeting_spell]

                        spellcaster["mp"] -= spell["cost"]
                        target_hero["hp"] = min(target_hero["max_hp"], target_hero["hp"] + spell["healing"])
                        target_hero["heal_flash"] = 30

                        combat_message = f"{spellcaster['name']} casts Heal on {target_hero['name']} for {spell['healing']} HP!"
                        if in_combat:
                            combat.turn_index += 1

                        targeting_spell = None
                        spellcaster = None
            elif viewing_spell_book is not None:
                if event.key == pygame.K_ESCAPE:
                    viewing_spell_book = None
                elif event.key == pygame.K_1:
                    select_spell_from_book(viewing_spell_book, 0)
                elif event.key == pygame.K_2:
                    select_spell_from_book(viewing_spell_book, 1)
            elif viewing_character is not None:
                if event.key == pygame.K_ESCAPE:
                    viewing_character = None
                elif event.key == pygame.K_1:
                    viewing_character = 0
                elif event.key == pygame.K_2:
                    viewing_character = 1
                elif event.key == pygame.K_3:
                    viewing_character = 2
                elif event.key == pygame.K_4:
                    viewing_character = 3
            else:
                if not in_combat and targeting_spell is None:
                    if event.key == pygame.K_1:
                        if selected_hero_index == 0:
                            viewing_character = 0
                        else:
                            selected_hero_index = 0
                    elif event.key == pygame.K_2:
                        if selected_hero_index == 1:
                            viewing_character = 1
                        else:
                            selected_hero_index = 1
                    elif event.key == pygame.K_3:
                        if selected_hero_index == 2:
                            viewing_character = 2
                        else:
                            selected_hero_index = 2
                    elif event.key == pygame.K_4:
                        if selected_hero_index == 3:
                            viewing_character = 3
                        else:
                            selected_hero_index = 3
                    elif event.key == pygame.K_c:
                        hero = party_members[selected_hero_index]
                        if hero.get("spells"):
                            viewing_spell_book = hero
                        else:
                            combat_message = f"{hero['name']} has no spells!"

                if in_combat and current_opponent and current_opponent["alive"]:
                    if current_actor and current_actor != current_opponent:
                        hero = current_actor
                        if hero["hp"] > 0:
                            if event.key == pygame.K_a:
                                if hero["weapon"] is not None:
                                    dmg = random.randint(
                                        hero["weapon"]["min_atk"], hero["weapon"]["max_atk"]
                                    )
                                else:
                                    dmg = 0
                                current_opponent["hp"] = max(
                                    0, current_opponent["hp"] - dmg
                                )

                                if current_opponent["hp"] <= 0:
                                    current_opponent["alive"] = False
                                    combat_message = f"Victory! {hero['name']} defeats the {current_opponent['name']}!"
                                    in_combat = False
                                    current_opponent = None
                                else:
                                    combat_message = (
                                        f"{hero['name']} attacks for {dmg} damage! Next turn..."
                                    )
                                    combat.turn_index += 1
                            elif event.key == pygame.K_c:
                                if hero.get("spells"):
                                    viewing_spell_book = hero
                                else:
                                    combat_message = f"{hero['name']} has no spell book!"
                            elif event.key == pygame.K_w:
                                combat_message = (
                                    f"{hero['name']} waits defensively. Next turn..."
                                )
                                combat.turn_index += 1
                else:
                    if not in_combat:
                        if event.key == pygame.K_F1:
                            load_level(1)
                        elif event.key == pygame.K_F2:
                            load_level(2)
                        elif event.key == pygame.K_F3:
                            load_level(3)
                        elif event.key == pygame.K_ESCAPE:
                            running = False

    if in_combat and current_opponent and current_opponent["alive"]:
        if combat.turn_index < len(combat.turn_queue):
            actor = combat.turn_queue[combat.turn_index]
            if "hp" in actor and actor["hp"] <= 0:
                combat.turn_index += 1
            elif actor == current_opponent:
                living_heroes = [h for h in party_members if h["hp"] > 0]
                if living_heroes:
                    if combat.has_line_of_sight(posX, posY, current_opponent["x"], current_opponent["y"]):
                        target = random.choice(living_heroes)
                        dmg = random.randint(
                            current_opponent["min_atk"], current_opponent["max_atk"]
                        )
                        target["hp"] = max(0, target["hp"] - dmg)
                        attack_flash_timer = 20
                        combat_message = f"{current_opponent['name']} attacks {target['name']} for {dmg} damage!"

                        if all(h["hp"] <= 0 for h in party_members):
                            combat_message = "Your party has fallen... Press ESC to quit."
                            current_opponent["alive"] = False
                            in_combat = False
                    else:
                        combat_message = f"{current_opponent['name']} cannot reach you through the wall!"
                combat.turn_index += 1
        else:
            combat.start_combat_round(current_opponent)

    if viewing_character is None and viewing_spell_book is None and targeting_spell is None and not in_combat:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            newX = posX + dirX * MOVE_SPEED
            newY = posY + dirY * MOVE_SPEED
            if combat.can_move_to(newX, posY, PLAYER_RADIUS):
                posX = newX
            if combat.can_move_to(posX, newY, PLAYER_RADIUS):
                posY = newY
        if keys[pygame.K_DOWN]:
            newX = posX - dirX * MOVE_SPEED
            newY = posY - dirY * MOVE_SPEED
            if combat.can_move_to(newX, posY, PLAYER_RADIUS):
                posX = newX
            if combat.can_move_to(posX, newY, PLAYER_RADIUS):
                posY = newY

        if keys[pygame.K_LEFT]:
            oldDirX = dirX
            dirX = dirX * math.cos(ROT_SPEED) - dirY * math.sin(ROT_SPEED)
            dirY = oldDirX * math.sin(ROT_SPEED) + dirY * math.cos(ROT_SPEED)
            oldPlaneX = planeX
            planeX = planeX * math.cos(ROT_SPEED) - planeY * math.sin(ROT_SPEED)
            planeY = oldPlaneX * math.sin(ROT_SPEED) + planeY * math.cos(ROT_SPEED)
        if keys[pygame.K_RIGHT]:
            oldDirX = dirX
            dirX = dirX * math.cos(-ROT_SPEED) - dirY * math.sin(-ROT_SPEED)
            dirY = oldDirX * math.sin(-ROT_SPEED) + dirY * math.cos(-ROT_SPEED)
            oldPlaneX = planeX
            planeX = planeX * math.cos(-ROT_SPEED) - planeY * math.sin(-ROT_SPEED)
            planeY = oldPlaneX * math.sin(-ROT_SPEED) + planeY * math.cos(-ROT_SPEED)

    # Check for enemy encounters only when exploring
    if viewing_character is None and viewing_spell_book is None and targeting_spell is None and not in_combat:
        enc_in_combat, enc_opp, dirX, dirY, planeX, planeY, enc_msg = combat.check_enemy_encounters(
            posX, posY, dirX, dirY, planeX, planeY, opponents, in_combat
        )
        if enc_in_combat and enc_opp:
            in_combat = True
            current_opponent = enc_opp
            combat_message = enc_msg
            combat.start_combat_round(current_opponent)

    # Render Ceiling / Sky and Floor on the 3D surface
    horizon = RENDER_HEIGHT // 2

    if level_data.get("sky"):
        screen.blit(sky_surface, (0, 0))
        draw_sun(screen, dirX, dirY, planeX, planeY)
    else:
        screen.fill(CEILING_COLOR, (0, 0, RENDER_WIDTH, horizon + 1))

    if floor_luts:
        lut = floor_luts[(pygame.time.get_ticks() // 250) % len(floor_luts)]
        floor_caster.draw(posX, posY, dirX, dirY, planeX, planeY,
                          floor_kind_lut, lut)
        scaled = pygame.transform.scale(
            floor_caster.band,
            (RENDER_WIDTH, RENDER_HEIGHT - horizon - 1),
        )
        screen.blit(scaled, (0, horizon + 1))
    else:
        screen.fill(FLOOR_COLOR, (0, horizon + 1, RENDER_WIDTH, RENDER_HEIGHT - horizon - 1))

    tex_res = 256
    ray_cache = []

    # Raycasting Pass
    for x in range(RENDER_WIDTH):
        cameraX = 2 * x / RENDER_WIDTH - 1
        rayDirX = dirX + planeX * cameraX
        rayDirY = dirY + planeY * cameraX

        mapX = int(posX)
        mapY = int(posY)

        deltaDistX = abs(1 / rayDirX) if rayDirX != 0 else 1e30
        deltaDistY = abs(1 / rayDirY) if rayDirY != 0 else 1e30

        hit = 0
        side = 0

        if rayDirX < 0:
            stepX = -1
            sideDistX = (posX - mapX) * deltaDistX
        else:
            stepX = 1
            sideDistX = (mapX + 1.0 - posX) * deltaDistX

        if rayDirY < 0:
            stepY = -1
            sideDistY = (posY - mapY) * deltaDistY
        else:
            stepY = 1
            sideDistY = (mapY + 1.0 - posY) * deltaDistY

        while hit == 0:
            if sideDistX < sideDistY:
                sideDistX += deltaDistX
                mapX += stepX
                side = 0
            else:
                sideDistY += deltaDistY
                mapY += stepY
                side = 1

            if combat.is_wall(mapX, mapY):
                hit = 1

        if side == 0:
            perpWallDist = (mapX - posX + (1 - stepX) / 2) / rayDirX
            wallX = posY + perpWallDist * rayDirY
        else:
            perpWallDist = (mapY - posY + (1 - stepY) / 2) / rayDirY
            wallX = posX + perpWallDist * rayDirX

        wallX -= math.floor(wallX)

        ray_cache.append({
            "perpWallDist": perpWallDist,
            "side": side,
            "wallX": wallX,
            "rayDirX": rayDirX,
            "rayDirY": rayDirY,
        })

    # Wall Rendering Pass using renderer.TEXTURE_STRIPS
    active_strips = renderer.TEXTURE_STRIPS[active_texture_id]
    for x in range(RENDER_WIDTH):
        data = ray_cache[x]
        perpWallDist = data["perpWallDist"]
        side = data["side"]
        wallX = data["wallX"]
        rayDirX = data["rayDirX"]
        rayDirY = data["rayDirY"]

        lineHeight = (
            max(1, int(RENDER_HEIGHT / perpWallDist))
            if perpWallDist > 0
            else RENDER_HEIGHT
        )
        drawStart = (RENDER_HEIGHT - lineHeight) // 2
        drawEnd = drawStart + lineHeight - 1

        texX = int(wallX * tex_res)
        if side == 0 and rayDirX < 0:
            texX = tex_res - texX - 1
        if side == 1 and rayDirY > 0:
            texX = tex_res - texX - 1

        try:
            wall_strip = active_strips[texX]
            scaled_strip = pygame.transform.scale(wall_strip, (1, lineHeight))

            if side == 1:
                darken = pygame.Surface((1, lineHeight))
                darken.fill((30, 30, 30))
                scaled_strip.blit(darken, (0, 0), special_flags=pygame.BLEND_SUB)

            screen.blit(scaled_strip, (x, drawStart))
        except ValueError:
            fallback_color = (130, 130, 140) if side == 0 else (100, 100, 110)
            pygame.draw.line(screen, fallback_color, (x, drawStart), (x, drawEnd))

    # Sort opponents by distance (Painter's Algorithm)
    sorted_opponents = sorted(opponents, key=lambda o: math.hypot(o["x"] - posX, o["y"] - posY), reverse=True)

    # Render opponents/sprites using procedural factory
    for opp in sorted_opponents:
        if opp["alive"]:
            spriteX = opp["x"] - posX
            spriteY = opp["y"] - posY

            invDet = 1.0 / (planeX * dirY - dirX * planeY)
            transformX = invDet * (dirY * spriteX - dirX * spriteY)
            transformY = invDet * (-planeY * spriteX + planeX * spriteY)

            if transformY > 0.2:
                screenX = int((RENDER_WIDTH / 2) * (1.0 + transformX / transformY))

                spriteHeight = abs(int(RENDER_HEIGHT / transformY * 1.35))
                spriteWidth = abs(int(RENDER_HEIGHT / transformY * 1.35))

                drawStartY = max(0, (RENDER_HEIGHT - spriteHeight) // 2)
                drawEndY = min(RENDER_HEIGHT, (RENDER_HEIGHT + spriteHeight) // 2)
                drawStartX = max(0, screenX - spriteWidth // 2)
                drawEndX = min(RENDER_WIDTH, screenX + spriteWidth // 2)

                if drawEndX <= drawStartX or drawEndY <= drawStartY:
                    continue

                visible = False
                check_stripes = [drawStartX, screenX, drawEndX - 1]
                for stripe in check_stripes:
                    if 0 <= stripe < RENDER_WIDTH:
                        if transformY <= ray_cache[stripe]["perpWallDist"]:
                            visible = True
                            break

                if not visible:
                    continue

                is_current = in_combat and current_opponent == opp
                body_color = (
                    (200, 60, 60)
                    if (is_current and (attack_flash_timer > 0 or spell_effect_timer > 0))
                    else (70, 190, 160)
                )
                breath = int(math.sin(pygame.time.get_ticks() * 0.008 + opp["x"]) * 6)

                ghost_surf = get_cached_procedural_goblin_ghost(
                    drawEndX - drawStartX,
                    drawEndY - drawStartY,
                    body_color,
                    breath,
                )

                screen.blit(ghost_surf, (drawStartX, drawStartY))

    if attack_flash_timer > 0:
        attack_flash_timer -= 1

    # Spell Visual Effect Rendering on Screen (Magic Arrow only)
    if spell_effect_timer > 0:
        spell_overlay = pygame.Surface((RENDER_WIDTH, RENDER_HEIGHT), pygame.SRCALPHA)
        spell_overlay.fill((80, 160, 255, 50 + spell_effect_timer * 4))
        screen.blit(spell_overlay, (0, 0))
        pygame.draw.circle(
            screen, (150, 220, 255),
            (RENDER_WIDTH // 2, RENDER_HEIGHT // 2),
            spell_effect_timer * 14, 3
        )
        spell_effect_timer -= 1

    # ==========================================
    # ASSEMBLE ON VIRTUAL MASTER SURFACE (840x740)
    # ==========================================
    game_surface.blit(screen, (0, 0))

    # Draw Targeting Modal Banner if targeting is active
    if targeting_spell is not None:
        banner_rect = pygame.Rect(40, 150, VIRTUAL_WIDTH - 80, 70)
        pygame.draw.rect(game_surface, (10, 40, 20), banner_rect)
        pygame.draw.rect(game_surface, (50, 255, 120), banner_rect, 3)

        banner_title = font_title.render("CHOOSE PARTY MEMBER TO HEAL", True, (100, 255, 150))
        banner_sub = font_med.render("Press party keys [1], [2], [3], or [4]  |  [ESC] to Cancel", True,
                                     (220, 240, 220))

        game_surface.blit(banner_title, banner_title.get_rect(center=(banner_rect.centerx, banner_rect.y + 22)))
        game_surface.blit(banner_sub, banner_sub.get_rect(center=(banner_rect.centerx, banner_rect.y + 48)))

    # Draw Combat Overlay if active
    elif in_combat and current_opponent and current_opponent["alive"]:
        combat_box = pygame.Rect(20, 40, VIRTUAL_WIDTH - 40, 80)
        pygame.draw.rect(game_surface, (15, 15, 20), combat_box)
        pygame.draw.rect(game_surface, (200, 50, 50), combat_box, 2)

        enemy_lbl = font_large.render(
            f"FIGHTING: {current_opponent['name']} (HP: {current_opponent['hp']}/{current_opponent['max_hp']})",
            True,
            (255, 100, 100),
        )
        turn_owner = (
            combat.turn_queue[combat.turn_index]["name"]
            if (combat.turn_queue and combat.turn_index < len(combat.turn_queue) and combat.turn_queue[
                combat.turn_index] != current_opponent)
            else "Enemy"
        )
        msg_lbl = font_med.render(
            f"[{turn_owner}'s Turn] {combat_message}", True, (240, 240, 240)
        )
        action_lbl = font_med.render(
            "Commands: [A] Attack  |  [C] Spell Book  |  [W] Wait", True, (200, 200, 100)
        )

        game_surface.blit(enemy_lbl, (combat_box.x + 15, combat_box.y + 10))
        game_surface.blit(msg_lbl, (combat_box.x + 15, combat_box.y + 35))
        game_surface.blit(action_lbl, (combat_box.x + 15, combat_box.y + 55))
    else:
        # Non-combat status message / guide overlay
        status_box = pygame.Rect(20, 40, VIRTUAL_WIDTH - 40, 36)
        pygame.draw.rect(game_surface, (15, 15, 20), status_box)
        pygame.draw.rect(game_surface, (80, 80, 100), status_box, 1)
        status_lbl = font_med.render(f"Status: {combat_message}  |  [1-4] Select (Press again for Sheet)  |  [C] Spells", True,
                                     (220, 220, 220))
        game_surface.blit(status_lbl, (status_box.x + 12, status_box.y + 8))

    # Draw Level Title Overlay & Dynamic Switch hints
    fullscreen_text = "[F11] Exit Fullscreen" if is_fullscreen else "[F11] Fullscreen"
    txt = font_med.render(
        f"Level: {level_data['name']} | [F1/F2] Switch Level | {fullscreen_text}",
        True,
        (240, 240, 240),
    )
    game_surface.blit(txt, (10, 10))

    # Draw Party UI at the bottom seamlessly with active character frame or target highlights
    if in_combat and combat.turn_queue and combat.turn_index < len(combat.turn_queue):
        current_actor = combat.turn_queue[combat.turn_index]
    else:
        current_actor = party_members[selected_hero_index]
    draw_party_ui(game_surface, current_actor=current_actor, targeting_active=(targeting_spell is not None))

    # Render Subscreens if active
    if viewing_spell_book is not None:
        draw_spell_book(game_surface, viewing_spell_book)
    elif viewing_character is not None:
        draw_character_subscreen(game_surface, party_members[viewing_character])

    # ==========================================
    # ASPECT-RATIO PRESERVED SCALING & CENTERING
    # ==========================================
    window.fill((0, 0, 0))  # Fill letterbox / pillarbox borders with black

    win_w, win_h = window.get_size()
    virtual_aspect = VIRTUAL_WIDTH / VIRTUAL_HEIGHT
    window_aspect = win_w / win_h if win_h > 0 else virtual_aspect

    if window_aspect > virtual_aspect:
        # Window is wider than game -> Pillarboxing (black bars on left and right)
        scaled_h = win_h
        scaled_w = int(scaled_h * virtual_aspect)
        scale_x = (win_w - scaled_w) // 2
        scale_y = 0
    else:
        # Window is taller than game -> Letterboxing (black bars on top and bottom)
        scaled_w = win_w
        scaled_h = int(scaled_w / virtual_aspect)
        scale_x = 0
        scale_y = (win_h - scaled_h) // 2

    scaled_output = pygame.transform.smoothscale(game_surface, (scaled_w, scaled_h))
    window.blit(scaled_output, (scale_x, scale_y))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
