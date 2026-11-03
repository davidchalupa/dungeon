import math
import random
import sys
import pygame

# Initialize Pygame
pygame.init()

# Window Display Resolution (Adjusted height to fit the bottom picture bar)
WINDOW_WIDTH, WINDOW_HEIGHT = 840, 720
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Dungeon Engine - High Speed & Bright")

# High-Resolution Rendering Surface for 3D View (Top portion)
RENDER_WIDTH, RENDER_HEIGHT = 1664, 546
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
        "weapon": dagger_item,
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

HERO_PORTRAIT_SIZE = 96

for hero in party_members:
  try:
    surf = pygame.image.load(hero["path"]).convert_alpha()
    hero["avatar"] = pygame.transform.scale(surf, (HERO_PORTRAIT_SIZE, HERO_PORTRAIT_SIZE))
  except Exception as e:
    fallback = pygame.Surface((HERO_PORTRAIT_SIZE, HERO_PORTRAIT_SIZE))
    fallback.fill((100, 100, 120))
    hero["avatar"] = fallback


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
        "opponents": [
            {
                "name": "Cave Goblin",
                "x": 3.0,
                "y": 1.5,
                "hp": 25,
                "max_hp": 25,
                "min_atk": 2,
                "max_atk": 5,
                "alive": True,
            },
            {
                "name": "Cave Goblin",
                "x": 9.5,
                "y": 1.5,
                "hp": 25,
                "max_hp": 25,
                "min_atk": 2,
                "max_atk": 5,
                "alive": True,
            },
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
        "opponents": [
            {
                "name": "Cave Goblin",
                "x": 6.5,
                "y": 3.5,
                "hp": 25,
                "max_hp": 25,
                "min_atk": 2,
                "max_atk": 5,
                "alive": True,
            }
        ],
    },
}

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

  total_width = WINDOW_WIDTH
  spacing = 160
  start_x = (WINDOW_WIDTH - (len(party_members) * spacing)) / 2
  start_y = 590

  for i, hero in enumerate(party_members):
    cx = start_x + i * spacing
    surface.blit(hero["avatar"], (cx, start_y))

    # Highlight frame if it's currently this character's turn
    if current_actor == hero:
      pygame.draw.rect(
          surface, (255, 215, 0), (cx - 3, start_y - 3, HERO_PORTRAIT_SIZE + 6, HERO_PORTRAIT_SIZE + 6), 3
      )

    # Name text
    name_txt = font_med.render(
        f"[{i+1}] {hero['name']}",
        True,
        (230, 230, 230) if hero["hp"] > 0 else (120, 120, 120),
    )
    name_rect = name_txt.get_rect(center=(cx + HERO_PORTRAIT_SIZE / 2, start_y + HERO_PORTRAIT_SIZE + 12))
    surface.blit(name_txt, name_rect)

    # HP Bar
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


# ==========================================
# PROCEDURAL TEXTURES (256x256) - ISOLATED RNG
# ==========================================
def create_running_bond_brick_texture():
  tex_size = 256
  surf = pygame.Surface((tex_size, tex_size))
  surf.fill((80, 80, 90))
  brick_h = 32
  brick_w = 64
  # Use an isolated local random generator so we don't mess up global gameplay randomness
  tex_rng = random.Random(42)

  for y in range(0, tex_size, brick_h):
    row_idx = y // brick_h
    offset = (row_idx % 2) * (brick_w // 2)
    pygame.draw.line(surf, (45, 45, 55), (0, y), (tex_size, y), 3)

    for x in range(-brick_w + offset, tex_size + brick_w, brick_w):
      bx = x + 2
      by = y + 3
      bw = brick_w - 4
      bh = brick_h - 4
      c_var = tex_rng.randint(-10, 10)
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
  tex_rng = random.Random(123)

  for y in range(tex_size):
    for x in range(tex_size):
      noise = (
          140
          + int(20 * math.sin(x * 0.1) * math.cos(y * 0.1))
          + tex_rng.randint(-15, 15)
      )
      color_val = max(80, min(230, noise))
      surf.set_at((x, y), (color_val, color_val, color_val + 10))
  return surf


TEXTURES = {
    1: create_running_bond_brick_texture(),
    2: create_organic_texture(),
}

# ==========================================
# MAIN GAME LOOP
# ==========================================
running = True
while running:
  # Get current combat actor if in combat
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
        # Character hotkeys work ANYTIME (exploration or combat)
        if event.key == pygame.K_1:
          viewing_character = 0
        elif event.key == pygame.K_2:
          viewing_character = 1
        elif event.key == pygame.K_3:
          viewing_character = 2
        elif event.key == pygame.K_4:
          viewing_character = 3
        elif in_combat and current_opponent and current_opponent["alive"]:
          # Combat controls (only active if it's a hero's turn)
          if current_actor and current_actor != current_opponent:
            hero = current_actor
            if hero["hp"] > 0:
              if event.key == pygame.K_a:
                # Single Hero Attack Action
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
                # Wait Action
                combat_message = (
                    f"{hero['name']} waits defensively. Next turn..."
                )
                turn_index += 1
        else:
          # Main Dungeon controls (exploration only)
          if event.key == pygame.K_5:
            load_level(1)
          elif event.key == pygame.K_6:
            load_level(2)
          elif event.key == pygame.K_ESCAPE:
            running = False

  # Handle automatic enemy turn in queue, or round advancement
  if in_combat and current_opponent and current_opponent["alive"]:
    if turn_index < len(turn_queue):
      actor = turn_queue[turn_index]
      # If it's a dead hero, skip their turn
      if "hp" in actor and actor["hp"] <= 0:
        turn_index += 1
      # If it's the enemy's turn, execute attack automatically
      elif actor == current_opponent:
        living_heroes = [h for h in party_members if h["hp"] > 0]
        if living_heroes:
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
        turn_index += 1
    else:
      # End of round queue reached; start a new randomized round
      start_combat_round()

  # Only process movement if not in combat and not viewing subscreen
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

    # Check proximity to any active opponent to trigger combat
    for opp in opponents:
      if opp["alive"]:
        dist_to_enemy = math.hypot(posX - opp["x"], posY - opp["y"])
        if dist_to_enemy < 2.5:
          in_combat = True
          current_opponent = opp
          start_combat_round()
          combat_message = (
              f"Encountered a {opp['name']}! Randomized combat started."
          )

          # Instantly turn player to face directly toward the triggered opponent
          toEnemyX = opp["x"] - posX
          toEnemyY = opp["y"] - posY
          dist = math.hypot(toEnemyX, toEnemyY)
          if dist > 0:
            dirX = toEnemyX / dist
            dirY = toEnemyY / dist
            planeX = dirY * 0.4
            planeY = -dirX * 0.4
          break

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

  # Render all alive opponents/sprites in the dungeon
  for opp in opponents:
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

        goblin_surf = pygame.Surface(
            (max(10, drawEndX - drawStartX), max(10, drawEndY - drawStartY)),
            pygame.SRCALPHA,
        )
        is_current = in_combat and current_opponent == opp
        body_color = (
            (180, 50, 50)
            if (is_current and attack_flash_timer > 0)
            else (60, 140, 70)
        )
        breath = int(math.sin(pygame.time.get_ticks() * 0.01 + opp["x"]) * 4)

        gw, gh = goblin_surf.get_width(), goblin_surf.get_height()
        pygame.draw.circle(
            goblin_surf, body_color, (gw // 2, gh // 3 + breath), gw // 4
        )
        pygame.draw.rect(
            goblin_surf,
            (40, 100, 50),
            (gw // 4, gh // 3 + breath, gw // 2, gh // 2),
        )
        pygame.draw.circle(
            goblin_surf, (255, 255, 0), (gw // 2 - 6, gh // 3 + breath - 2), 3
        )
        pygame.draw.circle(
            goblin_surf, (255, 255, 0), (gw // 2 + 6, gh // 3 + breath - 2), 3
        )

        screen.blit(goblin_surf, (drawStartX, drawStartY))

  if attack_flash_timer > 0:
    attack_flash_timer -= 1

  # Blit scaled 3D dungeon view onto the top of the main window
  scaled_window_surface = pygame.transform.smoothscale(
      screen, (WINDOW_WIDTH, WINDOW_HEIGHT)
  )
  window.blit(scaled_window_surface, (0, 0))

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
