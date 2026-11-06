import math
import random
import sys
import pygame

from assets.items import initialize_item_assets
from assets.levels import LEVELS
from assets.party_members import party_members
from engine.textures import TEXTURES

# Initialize Pygame
pygame.init()

# Window Display Resolution (Adjusted height to fit the bottom picture bar)
WINDOW_WIDTH, WINDOW_HEIGHT = 840, 720
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Dungeon Engine - High Speed & Bright")

# Optimized 3D Rendering Surface (Matched to window width)
RENDER_WIDTH, RENDER_HEIGHT = 840, 546
screen = pygame.Surface((RENDER_WIDTH, RENDER_HEIGHT))

clock = pygame.time.Clock()

# Load Fonts for UI
font_med = pygame.font.SysFont(None, 20)
font_large = pygame.font.SysFont(None, 24)

HERO_PORTRAIT_SIZE = 96


# Wrap asset loading in a function to prevent parser freeze on open
def initialize_hero_avatars():
    for hero in party_members:
        try:
            surf = pygame.image.load(hero["path"]).convert_alpha()
            hero["avatar"] = pygame.transform.scale(surf, (HERO_PORTRAIT_SIZE, HERO_PORTRAIT_SIZE))
        except Exception as e:
            fallback = pygame.Surface((HERO_PORTRAIT_SIZE, HERO_PORTRAIT_SIZE))
            fallback.fill((100, 100, 120))
            hero["avatar"] = fallback


initialize_hero_avatars()
initialize_item_assets()

current_level_id = 1
level_data = LEVELS[current_level_id]
WORLD_MAP = level_data["map"]
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

viewing_character = None
in_combat = False
current_opponent = None
turn_queue = []
turn_index = 0
combat_message = "An enemy blocks your path!"
attack_flash_timer = 0


def start_combat_round():
    global turn_queue, turn_index
    living_heroes = [h for h in party_members if h["hp"] > 0]
    if current_opponent and current_opponent["alive"]:
        turn_queue = living_heroes + [current_opponent]
        random.shuffle(turn_queue)
        turn_index = 0


def load_level(level_id):
    global current_level_id, level_data, WORLD_MAP
    global active_texture_id, posX, posY
    global dirX, dirY, planeX, planeY, opponents, in_combat, current_opponent

    current_level_id = level_id
    level_data = LEVELS[level_id]
    WORLD_MAP = level_data["map"]
    active_texture_id = level_data["texture_id"]

    posX, posY = 1.5, 1.5
    dirX, dirY = -1.0, 0.0
    planeX, planeY = 0.0, 0.4

    opponents = [dict(o) for o in level_data["opponents"]]
    in_combat = False
    current_opponent = None


def is_wall(x, y):
    map_height = len(WORLD_MAP)
    map_width = len(WORLD_MAP[0])
    if x < 0 or y < 0 or x >= map_width or y >= map_height:
        return True
    return WORLD_MAP[y][x] > 0


def can_move_to(x, y):
    for cx in (x - PLAYER_RADIUS, x + PLAYER_RADIUS):
        for cy in (y - PLAYER_RADIUS, y + PLAYER_RADIUS):
            if is_wall(math.floor(cx), math.floor(cy)):
                return False
    return True


# ==========================================
# PARTY UI RENDER (Bottom Bar with HP Bars & Turn Frame)
# ==========================================
def draw_party_ui(surface, current_actor=None):
    bar_rect = pygame.Rect(0, 580, WINDOW_WIDTH, 140)
    pygame.draw.rect(surface, (20, 20, 25), bar_rect)
    pygame.draw.line(surface, (50, 50, 60), (0, 580), (WINDOW_WIDTH, 580), 2)

    spacing = 160
    start_x = (WINDOW_WIDTH - (len(party_members) * spacing)) / 2
    start_y = 590

    for i, hero in enumerate(party_members):
        cx = start_x + i * spacing
        surface.blit(hero["avatar"], (cx, start_y))

        if current_actor == hero:
            pygame.draw.rect(
                surface, (255, 215, 0), (cx - 3, start_y - 3, HERO_PORTRAIT_SIZE + 6, HERO_PORTRAIT_SIZE + 6), 3
            )

        name_txt = font_med.render(
            f"[{i + 1}] {hero['name']}",
            True,
            (230, 230, 230) if hero["hp"] > 0 else (120, 120, 120),
        )
        name_rect = name_txt.get_rect(center=(cx + HERO_PORTRAIT_SIZE / 2, start_y + HERO_PORTRAIT_SIZE + 12))
        surface.blit(name_txt, name_rect)

        hp_bar_width = HERO_PORTRAIT_SIZE - 10
        hp_bar_height = 6
        hp_bar_x = cx + 5
        hp_bar_y = start_y + HERO_PORTRAIT_SIZE + 24

        bg_bar_rect = pygame.Rect(hp_bar_x, hp_bar_y, hp_bar_width, hp_bar_height)
        pygame.draw.rect(surface, (60, 30, 30), bg_bar_rect)

        hp_ratio = max(0.0, min(1.0, hero["hp"] / max(1, hero["max_hp"])))
        fill_width = int(hp_bar_width * hp_ratio)
        if fill_width > 0:
            fill_bar_rect = pygame.Rect(
                hp_bar_x, hp_bar_y, fill_width, hp_bar_height
            )
            bar_color = (50, 205, 50) if hero["hp"] > 0 else (150, 150, 150)
            pygame.draw.rect(surface, bar_color, fill_bar_rect)

        pygame.draw.rect(surface, (100, 100, 100), bg_bar_rect, 1)


# ==========================================
# CHARACTER SUBSCREEN RENDER
# ==========================================
def draw_character_subscreen(surface, hero):
    bg_rect = pygame.Rect(0, 0, WINDOW_WIDTH, 580)
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
        atk_str = (
            f"Attack: {hero['weapon']['min_atk']}-{hero['weapon']['max_atk']}"
        )
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


# Pre-cache texture vertical strips for performance
TEXTURE_STRIPS = {}
for tid, tex in TEXTURES.items():
    TEXTURE_STRIPS[tid] = [tex.subsurface((x, 0, 1, 256)) for x in range(256)]

# Modern Procedural Goblin Ghost Surface Cache with Fine 2-Pixel Quantization
goblin_ghost_surface_cache = {}


def get_cached_procedural_goblin_ghost(width, height, body_color, breath):
    target_w = max(10, width)
    target_h = max(10, height)

    # Quantize dimensions to nearest 2 pixels for buttery-smooth scaling with zero visual steps
    qw = max(10, (target_w + 1) // 2 * 2)
    qh = max(10, (target_h + 1) // 2 * 2)

    key = (qw, qh, body_color, breath)
    if key in goblin_ghost_surface_cache:
        return goblin_ghost_surface_cache[key]

    # Master canvas (256x256) with alpha channel for transparency & glow
    base_size = 256
    base_surf = pygame.Surface((base_size, base_size), pygame.SRCALPHA)

    cx = base_size // 2
    cy = base_size // 2 + breath

    # 1. Ethereal Aura (Soft outer glow)
    aura_color = (body_color[0], body_color[1], body_color[2], 50)
    pygame.draw.ellipse(base_surf, aura_color, (cx - 75, cy - 85, 150, 190))

    # 2. Wispy Ghostly Mantle & Flowing Tail
    body_points = [
        (cx, cy - 70),
        (cx - 52, cy - 18),
        (cx - 38, cy + 65),
        (cx - 16, cy + 92),
        (cx, cy + 78),
        (cx + 16, cy + 92),
        (cx + 38, cy + 65),
        (cx + 52, cy - 18),
    ]
    shroud_color = (body_color[0], body_color[1], body_color[2], 170)
    pygame.draw.polygon(base_surf, shroud_color, body_points)

    # 3. Spectral Goblin Head & Pointed Ears
    head_radius = 40
    head_center_y = cy - 35
    head_color = (body_color[0], body_color[1], body_color[2], 210)
    pygame.draw.circle(base_surf, head_color, (cx, head_center_y), head_radius)

    # Pointed Ears
    ear_left = [(cx - 32, head_center_y - 12), (cx - 78, head_center_y - 42), (cx - 38, head_center_y + 12)]
    ear_right = [(cx + 32, head_center_y - 12), (cx + 78, head_center_y - 42), (cx + 38, head_center_y + 12)]
    pygame.draw.polygon(base_surf, head_color, ear_left)
    pygame.draw.polygon(base_surf, head_color, ear_right)

    # Inner ear shading
    inner_color = (max(0, body_color[0] - 50), max(0, body_color[1] - 50), max(0, body_color[2] - 50), 190)
    pygame.draw.polygon(base_surf, inner_color, [(cx - 38, head_center_y - 6), (cx - 65, head_center_y - 30), (cx - 40, head_center_y + 8)])
    pygame.draw.polygon(base_surf, inner_color, [(cx + 38, head_center_y - 6), (cx + 65, head_center_y - 30), (cx + 40, head_center_y + 8)])

    # 4. Glowing Ethereal Eyes & Core Pupils
    eye_y = head_center_y - 4
    eye_offset = 17
    eye_rad = 7
    glow_eye_color = (240, 255, 120, 255) if body_color[0] < 150 else (255, 190, 190, 255)

    pygame.draw.circle(base_surf, glow_eye_color, (cx - eye_offset, eye_y), eye_rad)
    pygame.draw.circle(base_surf, glow_eye_color, (cx + eye_offset, eye_y), eye_rad)

    pupil_color = (255, 255, 255, 255)
    pygame.draw.circle(base_surf, pupil_color, (cx - eye_offset, eye_y), 3)
    pygame.draw.circle(base_surf, pupil_color, (cx + eye_offset, eye_y), 3)

    # Floating Spectral Magical Particles
    sparkle_color = (170, 255, 235, 160)
    pygame.draw.circle(base_surf, sparkle_color, (cx - 58, cy + 25), 4)
    pygame.draw.circle(base_surf, sparkle_color, (cx + 60, cy - 12), 5)
    pygame.draw.circle(base_surf, sparkle_color, (cx - 28, cy + 65), 3)
    pygame.draw.circle(base_surf, sparkle_color, (cx + 32, cy + 55), 4)

    # Smooth-scale to quantized size with alpha preservation
    scaled_surf = pygame.transform.smoothscale(base_surf, (qw, qh))
    goblin_ghost_surface_cache[key] = scaled_surf
    return scaled_surf


# ==========================================
# MAIN GAME LOOP
# ==========================================
running = True
while running:
    current_actor = None
    if in_combat and turn_queue and turn_index < len(turn_queue):
        current_actor = turn_queue[turn_index]

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if viewing_character is not None:
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
                if event.key == pygame.K_1:
                    viewing_character = 0
                elif event.key == pygame.K_2:
                    viewing_character = 1
                elif event.key == pygame.K_3:
                    viewing_character = 2
                elif event.key == pygame.K_4:
                    viewing_character = 3
                elif in_combat and current_opponent and current_opponent["alive"]:
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
                                    turn_index += 1
                            elif event.key == pygame.K_w:
                                combat_message = (
                                    f"{hero['name']} waits defensively. Next turn..."
                                )
                                turn_index += 1
                else:
                    if event.key == pygame.K_F1:
                        load_level(1)
                    elif event.key == pygame.K_F2:
                        load_level(2)
                    elif event.key == pygame.K_F3:
                        # Add next level ID here when ready, e.g., load_level(3)
                        pass
                    elif event.key == pygame.K_ESCAPE:
                        running = False

    if in_combat and current_opponent and current_opponent["alive"]:
        if turn_index < len(turn_queue):
            actor = turn_queue[turn_index]
            if "hp" in actor and actor["hp"] <= 0:
                turn_index += 1
            elif actor == current_opponent:
                living_heroes = [h for h in party_members if h["hp"] > 0]
                if living_heroes:
                    if has_line_of_sight(posX, posY, current_opponent["x"], current_opponent["y"]):
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
                turn_index += 1
        else:
            start_combat_round()

    if viewing_character is None and not in_combat:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            newX = posX + dirX * MOVE_SPEED
            newY = posY + dirY * MOVE_SPEED
            if can_move_to(newX, posY):
                posX = newX
            if can_move_to(posX, newY):
                posY = newY
        if keys[pygame.K_DOWN]:
            newX = posX - dirX * MOVE_SPEED
            newY = posY - dirY * MOVE_SPEED
            if can_move_to(newX, posY):
                posX = newX
            if can_move_to(posX, newY):
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
            planeY = (
                oldPlaneX * math.sin(-ROT_SPEED) + planeY * math.cos(-ROT_SPEED)
            )


        def check_ray_clear(x1, y1, x2, y2):
            dist = math.hypot(x2 - x1, y2 - y1)
            if dist == 0:
                return True
            steps = int(dist * 15)
            for i in range(steps + 1):
                t = i / max(1, steps)
                cx = x1 + (x2 - x1) * t
                cy = y1 + (y2 - y1) * t
                if is_wall(math.floor(cx), math.floor(cy)):
                    return False
            return True


        def has_line_of_sight(x1, y1, x2, y2):
            if not check_ray_clear(x1, y1, x2, y2):
                return False

            dx = x2 - x1
            dy = y2 - y1
            dist = math.hypot(dx, dy)
            if dist == 0:
                return True

            dirX = dx / dist
            dirY = dy / dist
            perpX = -dirY
            perpY = dirX
            offset = 0.22

            if not check_ray_clear(x1 + perpX * offset, y1 + perpY * offset, x2 + perpX * offset, y2 + perpY * offset):
                return False
            if not check_ray_clear(x1 - perpX * offset, y1 - perpY * offset, x2 - perpX * offset, y2 - perpY * offset):
                return False
            return True


        def check_enemy_encounters(posX, posY, dirX, dirY, planeX, planeY, opponents, in_combat):
            if in_combat:
                return in_combat, None, dirX, dirY, planeX, planeY, "An enemy blocks your path!"

            current_opp = None
            combat_msg = "An enemy blocks your path!"

            for opp in opponents:
                if opp["alive"]:
                    dist_to_enemy = math.hypot(posX - opp["x"], posY - opp["y"])
                    if dist_to_enemy < 2.5 and has_line_of_sight(posX, posY, opp["x"], opp["y"]):
                        in_combat = True
                        current_opp = opp
                        combat_msg = f"Encountered a {opp['name']}! Randomized combat started."

                        toEnemyX = opp["x"] - posX
                        toEnemyY = opp["y"] - posY
                        dist = math.hypot(toEnemyX, toEnemyY)
                        if dist > 0:
                            dirX = toEnemyX / dist
                            dirY = toEnemyY / dist
                            planeX = dirY * 0.4
                            planeY = -dirX * 0.4
                        break

            return in_combat, current_opp, dirX, dirY, planeX, planeY, combat_msg


        in_combat, current_opponent, dirX, dirY, planeX, planeY, combat_message = check_enemy_encounters(
            posX, posY, dirX, dirY, planeX, planeY, opponents, in_combat
        )
        if current_opponent:
            start_combat_round()

    # Render Ceiling and Floor on the 3D surface
    screen.fill(CEILING_COLOR, (0, 0, RENDER_WIDTH, RENDER_HEIGHT // 2))
    screen.fill(
        FLOOR_COLOR,
        (0, RENDER_HEIGHT // 2, RENDER_WIDTH, RENDER_HEIGHT // 2),
    )

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

            if is_wall(mapX, mapY):
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

    # Wall Rendering Pass
    active_strips = TEXTURE_STRIPS[active_texture_id]
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

    # Render all alive opponents/sprites using cached procedural surfaces & multi-column Z-buffer check
    for opp in sorted_opponents:
        if opp["alive"]:
            spriteX = opp["x"] - posX
            spriteY = opp["y"] - posY

            invDet = 1.0 / (planeX * dirY - dirX * planeY)
            transformX = invDet * (dirY * spriteX - dirX * spriteY)
            transformY = invDet * (-planeY * spriteX + planeX * spriteY)

            if transformY > 0.2:
                screenX = int((RENDER_WIDTH / 2) * (1.0 + transformX / transformY))

                # Proportional sizing
                spriteHeight = abs(int(RENDER_HEIGHT / transformY * 1.35))
                spriteWidth = abs(int(RENDER_HEIGHT / transformY * 1.35))

                drawStartY = max(0, (RENDER_HEIGHT - spriteHeight) // 2)
                drawEndY = min(RENDER_HEIGHT, (RENDER_HEIGHT + spriteHeight) // 2)
                drawStartX = max(0, screenX - spriteWidth // 2)
                drawEndX = min(RENDER_WIDTH, screenX + spriteWidth // 2)

                if drawEndX <= drawStartX or drawEndY <= drawStartY:
                    continue

                # Multi-Column Z-Buffer Check (Left edge, Center, Right edge)
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
                    if (is_current and attack_flash_timer > 0)
                    else (70, 190, 160)
                )
                breath = int(math.sin(pygame.time.get_ticks() * 0.008 + opp["x"]) * 6)

                # Fetch cached modern ghost sprite surface
                ghost_surf = get_cached_procedural_goblin_ghost(
                    drawEndX - drawStartX,
                    drawEndY - drawStartY,
                    body_color,
                    breath,
                )

                screen.blit(ghost_surf, (drawStartX, drawStartY))

    if attack_flash_timer > 0:
        attack_flash_timer -= 1

    # OPTIMIZED: Zero-Allocation Destination Scaling
    pygame.transform.smoothscale(screen, (WINDOW_WIDTH, WINDOW_HEIGHT), window)

    # Draw Combat Overlay if active
    if in_combat and current_opponent and current_opponent["alive"]:
        combat_box = pygame.Rect(20, 40, WINDOW_WIDTH - 40, 80)
        pygame.draw.rect(window, (15, 15, 20), combat_box)
        pygame.draw.rect(window, (200, 50, 50), combat_box, 2)

        enemy_lbl = font_large.render(
            f"FIGHTING: {current_opponent['name']} (HP: {current_opponent['hp']}/{current_opponent['max_hp']})",
            True,
            (255, 100, 100),
        )
        turn_owner = (
            current_actor["name"]
            if (current_actor and current_actor != current_opponent)
            else "Enemy"
        )
        msg_lbl = font_med.render(
            f"[{turn_owner}'s Turn] {combat_message}", True, (240, 240, 240)
        )
        action_lbl = font_med.render(
            "Commands: [A] Attack  |  [W] Wait", True, (200, 200, 100)
        )

        window.blit(enemy_lbl, (combat_box.x + 15, combat_box.y + 10))
        window.blit(msg_lbl, (combat_box.x + 15, combat_box.y + 35))
        window.blit(action_lbl, (combat_box.x + 15, combat_box.y + 55))

    # Draw Level Title Overlay & Switch hints
    txt = font_med.render(
        f"Level: {level_data['name']} | [5/6] Switch Level",
        True,
        (240, 240, 240),
    )
    window.blit(txt, (10, 10))

    # Draw Party UI at the bottom with active character frame
    draw_party_ui(window, current_actor=current_actor)

    # If a character subscreen is active, render it over the entire gameplay area
    if viewing_character is not None:
        draw_character_subscreen(window, party_members[viewing_character])

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
