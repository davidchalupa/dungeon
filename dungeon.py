import math
import random
import sys
import pygame

import numpy as np
from engine.floor_and_sky import FloorCaster, surface_to_array, make_sky, build_floor_luts, draw_sun

from engine.textures import FLOOR_TEXTURES

from assets.items import initialize_item_assets
from assets.levels import LEVELS
from assets.party_members import party_members, initialize_hero_avatars
from assets.spells import SPELLS
import engine.combat as combat
import engine.renderer as renderer
from engine.procedural_sprites import (
    get_cached_procedural_goblin_ghost,
    get_cached_procedural_cave_spider, SPIDER_ANIM_PHASES,
    get_cached_procedural_slime, SLIME_ANIM_PHASES,
)
from ui.hud import draw_party_ui, draw_character_subscreen, draw_spell_book
from ui.common import VIRTUAL_HEIGHT, VIRTUAL_WIDTH, initialize_fonts
from ui.map import draw_map


# Initialize Pygame
pygame.init()

# Virtual Logical Resolution (Maintains pristine UI and raycaster layout)
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
pygame.display.set_caption("Dungeon Engine")

# Optimized 3D Rendering Surface
screen = pygame.Surface((RENDER_WIDTH, RENDER_HEIGHT))

# Virtual Master Surface for entire UI & Game View
game_surface = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))

clock = pygame.time.Clock()

font_med, font_large, font_title = initialize_fonts()
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
resting_confirmation = False
map_visible = False
spellcaster = None
in_combat = False
current_opponent = None
combat_message = "Exploring the dungeon... Press [R] to Rest."
attack_flash_timer = 0
spell_effect_timer = 0
food_portions = 20

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

    posX, posY = level_data["init_pos"]["x"], level_data["init_pos"]["y"]
    dirX, dirY = -1.0, 0.0
    planeX, planeY = 0.0, 0.4

    opponents = [dict(o) for o in level_data["opponents"]]
    in_combat = False
    current_opponent = None
    combat_message = "Exploring the dungeon... Press [R] to Rest."

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
                        exp_reward = current_opponent.get("exp_reward", 0)
                        msg_suffix = combat.award_party_exp(exp_reward)
                        combat_message = f"Victory! {hero['name']} casts {s_name} and defeats the {current_opponent['name']}!{msg_suffix}"
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
            elif resting_confirmation:
                if event.key == pygame.K_y:
                    food_cost = len(party_members)
                    if food_portions >= food_cost:
                        food_portions -= food_cost
                        for hero in party_members:
                            hero["hp"] = hero["max_hp"]
                            if "max_mp" in hero:
                                hero["mp"] = hero["max_mp"]
                            else:
                                hero["mp"] = hero.get("mp", 50)
                        resting_confirmation = False
                        combat_message = f"The party rests, consuming {food_cost} food portions. HP & Mana restored!"
                    else:
                        resting_confirmation = False
                        combat_message = f"Not enough food to rest! Need {food_cost} portions (have {food_portions})."
                elif event.key in (pygame.K_n, pygame.K_ESCAPE):
                    resting_confirmation = False
                    combat_message = "Resting cancelled."
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
            elif map_visible:
                if event.key in (pygame.K_m, pygame.K_ESCAPE):
                    map_visible = False
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
                    elif event.key == pygame.K_r:
                        if not in_combat:
                            # Check if any alive opponent is within 5 cells
                            hostile_nearby = False
                            for opp in opponents:
                                if opp.get("alive", True):
                                    dist = math.hypot(opp["x"] - posX, opp["y"] - posY)
                                    if dist <= 8.0:
                                        hostile_nearby = True
                                        break

                            if hostile_nearby:
                                combat_message = "Cannot rest! Hostile creatures are nearby!"
                            else:
                                food_cost = len(party_members)
                                if food_portions >= food_cost:
                                    resting_confirmation = True
                                else:
                                    combat_message = f"Not enough food to rest! Need {food_cost} portions (have {food_portions})."
                        else:
                            combat_message = "Cannot rest while in combat!"
                    elif event.key == pygame.K_m:  # Toggle map
                        map_visible = True

                if in_combat and current_opponent and current_opponent["alive"]:
                    if current_actor and current_actor != current_opponent:
                        hero = current_actor
                        if hero["hp"] > 0:
                            if event.key == pygame.K_a:
                                dmg = combat.calculate_hero_attack_damage(hero, current_opponent)
                                current_opponent["hp"] = max(0, current_opponent["hp"] - dmg)

                                if current_opponent["hp"] <= 0:
                                    current_opponent["alive"] = False
                                    exp_reward = current_opponent.get("exp_reward", 250)
                                    msg_suffix = combat.award_party_exp(exp_reward)
                                    combat_message = f"Victory! {hero['name']} defeats the {current_opponent['name']}!{msg_suffix}"
                                    in_combat = False
                                    current_opponent = None
                                else:
                                    combat_message = f"{hero['name']} attacks for {dmg} damage! Next turn..."
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
                        elif event.key == pygame.K_F4:
                            load_level(4)
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
                        dmg = combat.calculate_damage(current_opponent, target)
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

    if viewing_character is None and viewing_spell_book is None and targeting_spell is None and not resting_confirmation and not in_combat and not map_visible:
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
    if viewing_character is None and viewing_spell_book is None and targeting_spell is None and not resting_confirmation and not in_combat and not map_visible:
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

        hit = 0  # 0 = searching, 1 = solid wall hit (1), 2 = open sea / horizon
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

            # Check map boundaries
            if mapX < 0 or mapX >= len(WORLD_MAP[0]) or mapY < 0 or mapY >= len(WORLD_MAP):
                hit = 2
                break

            cell_type = WORLD_MAP[mapY][mapX]
            if cell_type == 1:
                hit = 1  # Solid wall hits stop the ray
            elif cell_type == 2:
                pass  # Water cell (2): ray passes right through so FloorCaster renders the water!
            elif combat.is_wall(mapX, mapY):
                hit = 1

        if hit == 1:
            if side == 0:
                perpWallDist = (mapX - posX + (1 - stepX) / 2) / rayDirX
                wallX = posY + perpWallDist * rayDirY
            else:
                perpWallDist = (mapY - posY + (1 - stepY) / 2) / rayDirY
                wallX = posX + perpWallDist * rayDirX

            wallX -= math.floor(wallX)
        else:
            perpWallDist = float('inf')  # Infinite distance so sprites over water render properly
            wallX = 0

        ray_cache.append({
            "hit": hit,
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
        if data["hit"] != 1:
            continue  # Skip drawing walls for water/open sea (hit == 2 or 0)

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

                is_spider = opp.get("sprite") == "spider"
                is_slime = opp.get("sprite") == "slime"

                if is_spider:
                    sprite_scale = 0.55
                elif is_slime:
                    sprite_scale = 0.65
                else:
                    sprite_scale = 1.35

                spriteHeight = abs(int(RENDER_HEIGHT / transformY * sprite_scale))
                spriteWidth = abs(int(RENDER_HEIGHT / transformY * sprite_scale))

                # --- Shift bounding box down so entities sit flush on the floor ---
                if is_spider:
                    base_shift = int(spriteHeight * 0.42)
                    distance_boost = int(max(0, 80 - spriteHeight) * 0.35) if spriteHeight < 80 else 0
                    vertical_shift = base_shift + distance_boost
                elif is_slime:
                    base_shift = int(spriteHeight * 0.38)
                    distance_boost = int(max(0, 80 - spriteHeight) * 0.30) if spriteHeight < 80 else 0
                    vertical_shift = base_shift + distance_boost
                else:
                    vertical_shift = 0

                drawStartY = max(0, (RENDER_HEIGHT - spriteHeight) // 2 + vertical_shift)
                drawEndY = min(RENDER_HEIGHT, (RENDER_HEIGHT + spriteHeight) // 2 + vertical_shift)
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
                flashing = is_current and (attack_flash_timer > 0 or spell_effect_timer > 0)

                if is_spider:
                    anim_phase = (pygame.time.get_ticks() // 40) % SPIDER_ANIM_PHASES
                    spider_color = (180, 50, 40) if flashing else (45, 42, 40)
                    ghost_surf = get_cached_procedural_cave_spider(
                        drawEndX - drawStartX, drawEndY - drawStartY,
                        spider_color, anim_phase,
                    )
                elif is_slime:
                    anim_phase = (pygame.time.get_ticks() // 120) % SLIME_ANIM_PHASES
                    slime_color = (230, 80, 180) if flashing else (50, 210,
                                                                   100)  # Vibrant green, turns magenta when attacked!
                    ghost_surf = get_cached_procedural_slime(
                        drawEndX - drawStartX, drawEndY - drawStartY,
                        slime_color, anim_phase,
                    )
                else:
                    body_color = (200, 60, 60) if flashing else (70, 190, 160)
                    breath = int(math.sin(pygame.time.get_ticks() * 0.008 + opp["x"]) * 6)
                    ghost_surf = get_cached_procedural_goblin_ghost(
                        drawEndX - drawStartX, drawEndY - drawStartY,
                        body_color, breath,
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

    # Draw Rest Confirmation Modal Banner if active
    if resting_confirmation:
        rest_box = pygame.Rect(VIRTUAL_WIDTH // 2 - 210, VIRTUAL_HEIGHT // 2 - 60, 420, 120)
        pygame.draw.rect(game_surface, (15, 20, 35), rest_box)
        pygame.draw.rect(game_surface, (100, 180, 255), rest_box, 3)

        title_lbl = font_title.render("REST AT CAMP?", True, (150, 220, 255))
        sub_lbl1 = font_med.render(f"Restore HP/Mana? (Cost: {len(party_members)} Food | Have: {food_portions})", True,
                                   (220, 220, 220))
        sub_lbl2 = font_med.render("[Y] Yes, Rest  |  [N / ESC] Cancel", True, (255, 200, 100))

        game_surface.blit(title_lbl, title_lbl.get_rect(center=(rest_box.centerx, rest_box.y + 25)))
        game_surface.blit(sub_lbl1, sub_lbl1.get_rect(center=(rest_box.centerx, rest_box.y + 55)))
        game_surface.blit(sub_lbl2, sub_lbl2.get_rect(center=(rest_box.centerx, rest_box.y + 90)))

    # Draw Targeting Modal Banner if targeting is active
    elif targeting_spell is not None:
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

        # Wrap text to fit within box width and height
        max_width = VIRTUAL_WIDTH - 40
        text_to_render = f"Status: {combat_message} | [1-4] Select (Press again for Sheet) | [C] Spells | [R] Rest"
        lines = []
        words = text_to_render.split()

        current_line = ""
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            test_surface = font_med.render(test_line, True, (220, 220, 220))
            if test_surface.get_width() <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        line_height = font_med.get_linesize() if hasattr(font_med, 'get_linesize') else 12
        start_y = status_box.y + 8
        for i, line in enumerate(lines):
            y_pos = start_y + (i * line_height)
            surface_text = font_med.render(line, True, (220, 220, 220))
            game_surface.blit(surface_text, (status_box.x + 12, y_pos))

    # Draw Level Title Overlay & Dynamic Switch hints
    fullscreen_text = "[F11] Exit Fullscreen" if is_fullscreen else "[F11] Fullscreen"
    txt = font_med.render(
        f"{level_data['name']} | Food: {food_portions} | [F1/F2] Switch Level | {fullscreen_text}",
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

    # Render Subscreens & Overlays if active
    if map_visible:
        draw_map(
            game_surface,
            WORLD_MAP,
            (posX, posY),
            (dirX, dirY),
            opponents,
            level_name=level_data["name"],
            floor_texture_id=level_data.get("floor_texture_id"),
            texture_id=level_data.get("texture_id")
        )
    elif viewing_spell_book is not None:
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
        scaled_h = win_h
        scaled_w = int(scaled_h * virtual_aspect)
        scale_x = (win_w - scaled_w) // 2
        scale_y = 0
    else:
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
