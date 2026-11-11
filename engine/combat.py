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


def calculate_hero_attack_damage(hero, opponent):
    """Calculates physical damage dealt by a hero, reduced by the opponent's defense range."""
    if hero["weapon"] is not None:
        raw_dmg = random.randint(hero["weapon"]["min_atk"], hero["weapon"]["max_atk"])
    else:
        raw_dmg = 0

    def_min = opponent.get("min_def", 0)
    def_max = opponent.get("max_def", 0)
    def_reduction = random.randint(def_min, def_max) if def_max >= def_min else 0

    return max(0, raw_dmg - def_reduction)


def calculate_damage(opponent, target):
    """Calculates opponent damage reduced by a random number within the target's armor defense range."""
    raw_dmg = random.randint(opponent["min_atk"], opponent["max_atk"])
    armor = target.get("armor")

    if armor and "min_def" in armor and "max_def" in armor:
        def_reduction = random.randint(armor["min_def"], armor["max_def"])
        final_dmg = max(0, raw_dmg - def_reduction)
        return final_dmg

    return raw_dmg


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
    return active_map[y][x] == 1  # was: > 0


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


def award_party_exp(exp_amount):
    leveled_up_names = []
    for hero in party_members:
        if hero["hp"] > 0:  # Only living party members gain XP
            hero["exp"] = hero.get("exp", 0) + exp_amount

            # Total XP threshold for the next level
            next_level_exp = hero["level"] * (hero["level"] + 1) * 500

            while hero["exp"] >= next_level_exp:
                hero["level"] += 1

                # Increase ONLY the upper bound (max stats)
                hero["max_hp"] = hero["level"] * hero["hp_per_level"]
                hero["max_mp"] = hero["level"] * hero["mp_per_level"]

                # NOTE: We removed hero["hp"] = hero["max_hp"] and hero["mp"] = hero["max_mp"]
                # so current HP/MP remain at their current values without a full heal!

                leveled_up_names.append(hero["name"])
                next_level_exp = hero["level"] * (hero["level"] + 1) * 500

    if leveled_up_names:
        return f" Victory! Party gains {exp_amount} XP. LEVEL UP: {', '.join(leveled_up_names)}!"
    else:
        return f" Victory! Party gains {exp_amount} XP!"
