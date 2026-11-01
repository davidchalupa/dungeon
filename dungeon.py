import math
import random
import sys
import pygame

# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sharp High-Res Dungeon Engine (Optimized Proximity)")
clock = pygame.time.Clock()


# ==========================================
# HIGH-RES PROCEDURAL TEXTURES (256x256) - SHARP
# ==========================================
def create_brick_texture():
  tex_size = 256
  surf = pygame.Surface((tex_size, tex_size))
  surf.fill((110, 110, 120))  # Base gray stone color
  mortar_color = (45, 45, 55)

  brick_h = 32
  brick_w = 64
  for y in range(0, tex_size, brick_h):
    pygame.draw.line(surf, mortar_color, (0, y), (tex_size - 1, y), 3)

  for y_idx, y in enumerate(range(0, tex_size, brick_h)):
    offset = (y_idx % 2) * (brick_w // 2)
    for x in range(-offset, tex_size + brick_w, brick_w):
      pygame.draw.line(surf, mortar_color, (x, y), (x, y + brick_h), 3)

  return surf


def create_organic_texture():
  tex_size = 256
  surf = pygame.Surface((tex_size, tex_size))
  random.seed(123)

  for y in range(tex_size):
    for x in range(tex_size):
      noise = (
          100
          + int(20 * math.sin(x * 0.1) * math.cos(y * 0.1))
          + random.randint(-18, 18)
      )
      color_val = max(40, min(200, noise))
      surf.set_at((x, y), (color_val, color_val, color_val + 5))

  return surf


# Texture Registry (1 = Default Brick Mesh, 2 = Alternative Organic Stone)
TEXTURES = {
    1: create_brick_texture(),
    2: create_organic_texture(),
}

# ==========================================
# LEVEL & MAP CONFIGURATIONS
# ==========================================
LEVELS = {
    1: {
        "name": "Level 1: The Stone Keep (Default Bricks)",
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

# Player Position & Camera Parameters
posX, posY = 1.5, 1.5
dirX, dirY = -1.0, 0.0
planeX, planeY = 0.0, 0.4  # Balanced FOV to minimize edge skewing

MOVE_SPEED = 0.04
ROT_SPEED = 0.035
PLAYER_RADIUS = (
    0.42  # Larger buffer prevents getting close enough to trigger wall-shearing
)

CEILING_COLOR = (25, 25, 35)
FLOOR_COLOR = (45, 40, 35)


def load_level(level_id):
  global current_level_id, level_data, WORLD_MAP, active_texture_id, posX, posY, dirX, dirY
  current_level_id = level_id
  level_data = LEVELS[level_id]
  WORLD_MAP = level_data["map"]
  active_texture_id = level_data["texture_id"]
  posX, posY = 1.5, 1.5
  dirX, dirY = -1.0, 0.0


def can_move_to(x, y):
  for cx in [x - PLAYER_RADIUS, x + PLAYER_RADIUS]:
    for cy in [y - PLAYER_RADIUS, y + PLAYER_RADIUS]:
      if WORLD_MAP[int(cx)][int(cy)] > 0:
        return False
  return True


# Main Game Loop
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

  # Movement handling with collision buffer
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

  # Rotation handling
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

  # Background render
  screen.fill(CEILING_COLOR, (0, 0, WIDTH, HEIGHT // 2))
  screen.fill(FLOOR_COLOR, (0, HEIGHT // 2, WIDTH, HEIGHT // 2))

  current_texture = TEXTURES[active_texture_id]
  tex_res = 256

  # Raycasting Loop
  for x in range(WIDTH):
    cameraX = 2 * x / WIDTH - 1
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
      if WORLD_MAP[mapX][mapY] > 0:
        hit = 1

    if side == 0:
      perpWallDist = (mapX - posX + (1 - stepX) / 2) / rayDirX
    else:
      perpWallDist = (mapY - posY + (1 - stepY) / 2) / rayDirY

    lineHeight = int(HEIGHT / perpWallDist) if perpWallDist > 0 else HEIGHT

    drawStart = -lineHeight // 2 + HEIGHT // 2
    drawStart = max(0, drawStart)
    drawEnd = lineHeight // 2 + HEIGHT // 2
    drawEnd = min(HEIGHT - 1, drawEnd)

    # Texture coordinate mapping
    if side == 0:
      wallX = posY + perpWallDist * rayDirY
    else:
      wallX = posX + perpWallDist * rayDirX
    wallX -= math.floor(wallX)

    texX = int(wallX * tex_res)
    if side == 0 and rayDirX > 0:
      texX = tex_res - texX - 1
    if side == 1 and rayDirY < 0:
      texX = tex_res - texX - 1

    try:
      wall_strip = current_texture.subsurface((texX, 0, 1, tex_res))
      scaled_strip = pygame.transform.scale(wall_strip, (1, lineHeight))

      # Shading on side walls for depth
      if side == 1:
        darken = pygame.Surface((1, lineHeight))
        darken.fill((60, 60, 60))
        scaled_strip.blit(darken, (0, 0), special_flags=pygame.BLEND_SUB)

      screen.blit(scaled_strip, (x, drawStart))
    except ValueError:
      fallback_color = (110, 110, 120) if side == 0 else (80, 80, 90)
      pygame.draw.line(screen, fallback_color, (x, drawStart), (x, drawEnd))

  # On-screen HUD instructions
  font = pygame.font.SysFont(None, 22)
  txt = font.render(
      f"Level: {level_data['name']} | Switch: [1] Bricks, [2] Cavern",
      True,
      (220, 220, 220),
  )
  screen.blit(txt, (10, 10))

  pygame.display.flip()
  clock.tick(60)

pygame.quit()
sys.exit()
