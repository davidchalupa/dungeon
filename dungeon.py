import math
import random
import sys
import pygame

# Initialize Pygame
pygame.init()

# Window Display Resolution (Adjusted height to fit the bottom picture bar)
WINDOW_WIDTH, WINDOW_HEIGHT = 640, 540
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Dungeon Engine - High Speed & Bright")

# High-Resolution Rendering Surface for 3D View (Top portion)
RENDER_WIDTH, RENDER_HEIGHT = 1280, 420
screen = pygame.Surface((RENDER_WIDTH, RENDER_HEIGHT))

clock = pygame.time.Clock()

# Load Fonts for UI
font_med = pygame.font.SysFont(None, 20)
font_large = pygame.font.SysFont(None, 24)

# ==========================================
# ITEM DEFINITIONS & ASSETS
# ==========================================
longsword_item = {
    "name": "Longsword",
    "min_atk": 4,
    "max_atk": 8,
    "path": "images/longsword.png",
}

# Load and scale longsword icon
try:
  sword_surf = pygame.image.load(longsword_item["path"]).convert_alpha()
  longsword_item["icon"] = pygame.transform.scale(sword_surf, (34, 34))
except Exception as e:
  print(
      f"Warning: Could not load '{longsword_item['path']}' ({e}). Using"
      " placeholder."
  )
  fallback = pygame.Surface((34, 34))
  fallback.fill((140, 140, 160))
  longsword_item["icon"] = fallback

dagger_item = {
    "name": "Dagger",
    "min_atk": 2,
    "max_atk": 4,
    "path": "images/dagger.png",
}

# Load and scale dagger icon
try:
  dagger_surf = pygame.image.load(dagger_item["path"]).convert_alpha()
  dagger_item["icon"] = pygame.transform.scale(dagger_surf, (34, 34))
except Exception as e:
  print(
      f"Warning: Could not load '{dagger_item['path']}' ({e}). Using"
      " placeholder."
  )
  fallback = pygame.Surface((34, 34))
  fallback.fill((160, 140, 140))
  dagger_item["icon"] = fallback

# ==========================================
# PARTY DATA & ASSETS LOADING
# ==========================================
party_members = [
    {
        "name": "Thorne",
        "class": "Warrior",
        "path": "images/male-warrior.jpg",
        "hp": 10,
        "max_hp": 10,
        "mp": 0,
        "max_mp": 0,
        "weapon": longsword_item,
    },
    {
        "name": "Lyra",
        "class": "Mage",
        "path": "images/female-mage.jpg",
        "hp": 5,
        "max_hp": 5,
        "mp": 10,
        "max_mp": 10,
        "weapon": dagger_item,  # Equipped with Dagger
    },
    {
        "name": "Reece",
        "class": "Warrior",
        "path": "images/male-warrior-2.jpg",
        "hp": 10,
        "max_hp": 10,
        "mp": 0,
        "max_mp": 0,
        "weapon": longsword_item,
    },
    {
        "name": "Vesper",
        "class": "Ranger",
        "path": "images/female-ranger.jpg",
        "hp": 8,
        "max_hp": 8,
        "mp": 3,
        "max_mp": 3,
        "weapon": longsword_item,
    },
]

# Load and scale each character's avatar
for hero in party_members:
  try:
    surf = pygame.image.load(hero["path"]).convert_alpha()
    hero["avatar"] = pygame.transform.scale(surf, (80, 80))
  except Exception as e:
    print(
        f"Warning: Could not load '{hero['path']}' ({e}). Using placeholder."
    )
    fallback = pygame.Surface((80, 80))
    fallback.fill((100, 100, 120))
    hero["avatar"] = fallback


# ==========================================
# PARTY UI RENDER (Bottom Bar)
# ==========================================
def draw_party_ui(surface):
  # Bottom background bar
  bar_rect = pygame.Rect(0, 420, WINDOW_WIDTH, 120)
  pygame.draw.rect(surface, (20, 20, 25), bar_rect)
  pygame.draw.line(surface, (50, 50, 60), (0, 420), (WINDOW_WIDTH, 420), 2)

  # Layout spacing for avatars centered at the bottom
  start_x = 40
  spacing = 160
  start_y = 432

  for i, hero in enumerate(party_members):
    cx = start_x + i * spacing

    # Draw unique picture for this hero
    surface.blit(hero["avatar"], (cx, start_y))

    # Draw name and hotkey hint below picture
    name_txt = font_med.render(
        f"[{i+1}] {hero['name']}", True, (230, 230, 230)
    )
    name_rect = name_txt.get_rect(center=(cx + 40, start_y + 80 + 12))
    surface.blit(name_txt, name_rect)


# ==========================================
# CHARACTER SUBSCREEN RENDER (Full Screen View)
# ==========================================
def draw_character_subscreen(surface, hero):
  # Background covering the entire gameplay screen above the bottom panel
  bg_rect = pygame.Rect(0, 0, WINDOW_WIDTH, 420)
  pygame.draw.rect(surface, (22, 22, 28), bg_rect)
  pygame.draw.rect(surface, (160, 140, 90), bg_rect, 3)

  # Title Header
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

  # Top-Left: Avatar & Stats
  avatar_x = bg_rect.x + 25
  avatar_y = bg_rect.y + 60
  surface.blit(hero["avatar"], (avatar_x, avatar_y))

  stats_x = avatar_x + 95
  stats_y = avatar_y + 5
  name_txt = font_large.render(hero["name"], True, (255, 255, 255))
  class_txt = font_med.render(f"Class: {hero['class']}", True, (180, 180, 190))
  hp_txt = font_med.render(
      f"Hit Points: {hero['hp']} / {hero['max_hp']}", True, (120, 220, 120)
  )
  mp_txt = font_med.render(
      f"Mana: {hero['mp']} / {hero['max_mp']}", True, (120, 180, 255)
  )

  # Calculate Attack based on equipped weapon
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

  # Center: Hero Silhouette & 40x40 Equipment Slots
  sil_center_x = bg_rect.centerx
  sil_center_y = bg_rect.centery + 30
  sil_color = (55, 55, 70)

  # Silhouette body shapes
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

  # Armor Slot (Center of chest - 40x40, empty)
  armor_slot_rect = pygame.Rect(sil_center_x - 20, sil_center_y - 40, 40, 40)
  pygame.draw.rect(surface, (30, 30, 38), armor_slot_rect)
  pygame.draw.rect(surface, (110, 100, 70), armor_slot_rect, 2)

  # Weapon Slot (Square at character's right hand / left side - 40x40)
  weapon_slot_rect = pygame.Rect(sil_center_x - 80, sil_center_y - 20, 40, 40)
  pygame.draw.rect(surface, (30, 30, 38), weapon_slot_rect)
  pygame.draw.rect(surface, (110, 100, 70), weapon_slot_rect, 2)

  # Draw weapon icon if equipped
  if hero["weapon"] is not None and "icon" in hero["weapon"]:
    icon_rect = hero["weapon"]["icon"].get_rect(center=weapon_slot_rect.center)
    surface.blit(hero["weapon"]["icon"], icon_rect)

  # Footer Instructions
  footer_txt = font_med.render(
      "Press [ESC] to return to Dungeon", True, (170, 170, 170)
  )
  surface.blit(footer_txt, footer_txt.get_rect(center=(bg_rect.centerx, 390)))


# ==========================================
# PROCEDURAL TEXTURES (256x256)
# ==========================================
def create_running_bond_brick_texture():
  tex_size = 256
  surf = pygame.Surface((tex_size, tex_size))
  surf.fill((80, 80, 90))

  brick_h = 32
  brick_w = 64
  random.seed(42)

  for y in range(0, tex_size, brick_h):
    row_idx = y // brick_h
    offset = (row_idx % 2) * (brick_w // 2)
    pygame.draw.line(surf, (45, 45, 55), (0, y), (tex_size, y), 3)

    for x in range(-brick_w + offset, tex_size + brick_w, brick_w):
      bx = x + 2
      by = y + 3
      bw = brick_w - 4
      bh = brick_h - 4

      c_var = random.randint(-10, 10)
      brick_color = (
          max(100, min(190, 135 + c_var)),
          max(100, min(190, 135 + c_var)),
          max(110, min(200, 145 + c_var)),
      )
      pygame.draw.rect(surf, brick_color, (bx, by, bw, bh))
      pygame.draw.line(
          surf, (45, 45, 55), (x + brick_w, y), (x + brick_w, y + brick_h), 3
      )

  return surf


def create_organic_texture():
  tex_size = 256
  surf = pygame.Surface((tex_size, tex_size))
  random.seed(123)

  for y in range(tex_size):
    for x in range(tex_size):
      noise = (
          140
          + int(20 * math.sin(x * 0.1) * math.cos(y * 0.1))
          + random.randint(-15, 15)
      )
      color_val = max(80, min(230, noise))
      surf.set_at((x, y), (color_val, color_val, color_val + 10))

  return surf


TEXTURES = {
    1: create_running_bond_brick_texture(),
    2: create_organic_texture(),
}

# ==========================================
# LEVEL & MAP CONFIGURATIONS
# ==========================================
LEVELS = {
    1: {
        "name": "Level 1: The Stone Keep",
        "texture_id": 1,
        "map": [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1],
            [1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1],
            [1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1],
            [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        ],
    },
    2: {
        "name": "Level 2: The Deep Cavern",
        "texture_id": 2,
        "map": [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
            [1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
            [1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1],
            [1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        ],
    },
}

current_level_id = 1
level_data = LEVELS[current_level_id]
WORLD_MAP = level_data["map"]
active_texture_id = level_data["texture_id"]

posX, posY = 1.5, 1.5
dirX, dirY = -1.0, 0.0
planeX, planeY = 0.0, 0.4

MOVE_SPEED = 0.04
ROT_SPEED = 0.035
PLAYER_RADIUS = 0.22

CEILING_COLOR = (40, 40, 50)
FLOOR_COLOR = (60, 50, 40)

# Game State Variable for Character Sheets
viewing_character = None


def load_level(level_id):
  global current_level_id, level_data, WORLD_MAP
  global active_texture_id, posX, posY
  global dirX, dirY, planeX, planeY

  current_level_id = level_id
  level_data = LEVELS[level_id]
  WORLD_MAP = level_data["map"]
  active_texture_id = level_data["texture_id"]

  posX, posY = 1.5, 1.5
  dirX, dirY = -1.0, 0.0
  planeX, planeY = 0.0, 0.4


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
# MAIN GAME LOOP
# ==========================================
running = True
while running:
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      running = False
    elif event.type == pygame.KEYDOWN:
      if viewing_character is not None:
        # Subscreen controls
        if event.key == pygame.K_ESCAPE:
          viewing_character = None
      else:
        # Main Dungeon controls
        if event.key == pygame.K_1:
          viewing_character = 0
        elif event.key == pygame.K_2:
          viewing_character = 1
        elif event.key == pygame.K_3:
          viewing_character = 2
        elif event.key == pygame.K_4:
          viewing_character = 3
        elif event.key == pygame.K_5:
          load_level(1)
        elif event.key == pygame.K_6:
          load_level(2)
        elif event.key == pygame.K_ESCAPE:
          running = False

  # Only process movement if not viewing a character subscreen
  if viewing_character is None:
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

  # Render Ceiling and Floor on the 3D surface
  screen.fill(CEILING_COLOR, (0, 0, RENDER_WIDTH, RENDER_HEIGHT // 2))
  screen.fill(
      FLOOR_COLOR,
      (0, RENDER_HEIGHT // 2, RENDER_WIDTH, RENDER_HEIGHT // 2),
  )

  current_texture = TEXTURES[active_texture_id]
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
      wall_strip = current_texture.subsurface((texX, 0, 1, tex_res))
      scaled_strip = pygame.transform.scale(wall_strip, (1, lineHeight))

      if side == 1:
        darken = pygame.Surface((1, lineHeight))
        darken.fill((30, 30, 30))
        scaled_strip.blit(darken, (0, 0), special_flags=pygame.BLEND_SUB)

      screen.blit(scaled_strip, (x, drawStart))
    except ValueError:
      fallback_color = (130, 130, 140) if side == 0 else (100, 100, 110)
      pygame.draw.line(screen, fallback_color, (x, drawStart), (x, drawEnd))

  # Blit scaled 3D dungeon view onto the top of the main window
  scaled_window_surface = pygame.transform.smoothscale(
      screen, (WINDOW_WIDTH, 420)
  )
  window.blit(scaled_window_surface, (0, 0))

  # Draw Level Title Overlay & Switch hints
  txt = font_med.render(
      f"Level: {level_data['name']} | [5/6] Switch Level",
      True,
      (240, 240, 240),
  )
  window.blit(txt, (10, 10))

  # Draw Party UI at the bottom
  draw_party_ui(window)

  # If a character subscreen is active, render it over the entire gameplay area
  if viewing_character is not None:
    draw_character_subscreen(window, party_members[viewing_character])

  pygame.display.flip()
  clock.tick(60)

pygame.quit()
sys.exit()
