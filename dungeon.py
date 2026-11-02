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

# Load Font for UI
font_med = pygame.font.SysFont(None, 20)

# ==========================================
# PARTY DATA & ASSETS LOADING
# ==========================================
party_members = [
    {
        "name": "Thorne",
        "class": "Warrior",
        "path": "images/male-warrior.jpg",
    },
    {
        "name": "Lyra",
        "class": "Mage",
        "path": "images/female-mage.jpg",
    },
    {
        "name": "Vesper",
        "class": "Ranger",
        "path": "images/female-ranger.jpg",
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
# PARTY UI RENDER (Pictures & Names Only)
# ==========================================
def draw_party_ui(surface):
  # Bottom background bar
  bar_rect = pygame.Rect(0, 420, WINDOW_WIDTH, 120)
  pygame.draw.rect(surface, (20, 20, 25), bar_rect)
  pygame.draw.line(surface, (50, 50, 60), (0, 420), (WINDOW_WIDTH, 420), 2)

  # Layout spacing for 3 avatars centered at the bottom
  start_x = 110
  spacing = 160
  start_y = 432

  for i, hero in enumerate(party_members):
    cx = start_x + i * spacing

    # Draw unique picture for this hero
    surface.blit(hero["avatar"], (cx, start_y))

    # Draw name below picture
    name_txt = font_med.render(hero["name"], True, (230, 230, 230))
    name_rect = name_txt.get_rect(center=(cx + 40, start_y + 80 + 12))
    surface.blit(name_txt, name_rect)


# ==========================================
# PROCEDURAL TEXTURES (256x256) - VIBRANT & FAST
# ==========================================
def create_running_bond_brick_texture():
  tex_size = 256
  surf = pygame.Surface((tex_size, tex_size))
  surf.fill((80, 80, 90))  # Bright, crisp base mortar background

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
        "name": "Level 1: The Stone Keep (Running Bond Bricks)",
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
        "name": "Level 2: The Deep Cavern (Organic Stone)",
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
      if event.key == pygame.K_1:
        load_level(1)
      elif event.key == pygame.K_2:
        load_level(2)

  keys = pygame.key.get_pressed()
  if keys[pygame.K_ESCAPE]:
    running = False

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

  # Draw Level Title Overlay
  txt = font_med.render(
      f"Level: {level_data['name']} | Switch: [1] Bricks, [2] Cavern",
      True,
      (240, 240, 240),
  )
  window.blit(txt, (10, 10))

  # Draw Party UI at the bottom
  draw_party_ui(window)

  pygame.display.flip()
  clock.tick(60)

pygame.quit()
sys.exit()
