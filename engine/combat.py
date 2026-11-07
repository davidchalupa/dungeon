import math
import random

from assets.party_members import party_members

# Module-level map reference
WORLD_MAP = []
turn_queue = []
turn_index = 0


def start_combat_round(current_opponent):
    global turn_queue, turn_index
    living_heroes = [h for h in party_members if h["hp"] > 0]
    if current_opponent and current_opponent["alive"]:
        turn_queue = living_heroes + [current_opponent]
        random.shuffle(turn_queue)
        turn_index = 0

def is_water(x, y, map_data=None):
    active_map = map_data if map_data is not None else WORLD_MAP
    map_height = len(active_map)
    map_width = len(active_map[0])
    if x < 0 or y < 0 or x >= map_width or y >= map_height:
        return False
    return active_map[y][x] == 2


def is_wall(x, y, map_data=None):
    active_map = map_data if map_data is not None else WORLD_MAP
    map_height = len(active_map)
    map_width = len(active_map[0])
    if x < 0 or y < 0 or x >= map_width or y >= map_height:
        return True
    return active_map[y][x] == 1        # was: > 0


def can_move_to(x, y, PLAYER_RADIUS):
    for cx in (x - PLAYER_RADIUS, x + PLAYER_RADIUS):
        for cy in (y - PLAYER_RADIUS, y + PLAYER_RADIUS):
            if is_wall(math.floor(cx), math.floor(cy)):
                return False
            if is_water(math.floor(cx), math.floor(cy)):
                return False
    return True


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
                combat_msg = f"Encountered a {opp['name']}! Combat started."

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
