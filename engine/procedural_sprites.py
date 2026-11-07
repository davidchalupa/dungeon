import pygame

goblin_ghost_surface_cache = {}


def get_cached_procedural_goblin_ghost(width, height, body_color, breath):
    target_w = max(10, width)
    target_h = max(10, height)

    # If you want full resolution sprites (recommended for sharp visuals):
    qw = target_w
    qh = target_h

    # (Alternatively, if you wanted half-resolution for performance, use: qw = max(10, target_w // 2))

    key = (qw, qh, body_color, breath)
    if key in goblin_ghost_surface_cache:
        return goblin_ghost_surface_cache[key]

    base_size = 256
    base_surf = pygame.Surface((base_size, base_size), pygame.SRCALPHA)

    cx = base_size // 2
    cy = base_size // 2 + breath

    aura_color = (body_color[0], body_color[1], body_color[2], 50)
    pygame.draw.ellipse(base_surf, aura_color, (cx - 75, cy - 85, 150, 190))

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

    head_radius = 40
    head_center_y = cy - 35
    head_color = (body_color[0], body_color[1], body_color[2], 210)
    pygame.draw.circle(base_surf, head_color, (cx, head_center_y), head_radius)

    ear_left = [(cx - 32, head_center_y - 12), (cx - 78, head_center_y - 42), (cx - 38, head_center_y + 12)]
    ear_right = [(cx + 32, head_center_y - 12), (cx + 78, head_center_y - 42), (cx + 38, head_center_y + 12)]
    pygame.draw.polygon(base_surf, head_color, ear_left)
    pygame.draw.polygon(base_surf, head_color, ear_right)

    inner_color = (max(0, body_color[0] - 50), max(0, body_color[1] - 50), max(0, body_color[2] - 50), 190)
    pygame.draw.polygon(base_surf, inner_color,
                        [(cx - 38, head_center_y - 6), (cx - 65, head_center_y - 30), (cx - 40, head_center_y + 8)])
    pygame.draw.polygon(base_surf, inner_color,
                        [(cx + 38, head_center_y - 6), (cx + 65, head_center_y - 30), (cx + 40, head_center_y + 8)])

    eye_y = head_center_y - 4
    eye_offset = 17
    eye_rad = 7
    glow_eye_color = (240, 255, 120, 255) if body_color[0] < 150 else (255, 190, 190, 255)

    pygame.draw.circle(base_surf, glow_eye_color, (cx - eye_offset, eye_y), eye_rad)
    pygame.draw.circle(base_surf, glow_eye_color, (cx + eye_offset, eye_y), eye_rad)

    pupil_color = (255, 255, 255, 255)
    pygame.draw.circle(base_surf, pupil_color, (cx - eye_offset, eye_y), 3)
    pygame.draw.circle(base_surf, pupil_color, (cx + eye_offset, eye_y), 3)

    sparkle_color = (170, 255, 235, 160)
    pygame.draw.circle(base_surf, sparkle_color, (cx - 58, cy + 25), 4)
    pygame.draw.circle(base_surf, sparkle_color, (cx + 60, cy - 12), 5)
    pygame.draw.circle(base_surf, sparkle_color, (cx - 28, cy + 65), 3)
    pygame.draw.circle(base_surf, sparkle_color, (cx + 32, cy + 55), 4)

    scaled_surf = pygame.transform.smoothscale(base_surf, (qw, qh))
    goblin_ghost_surface_cache[key] = scaled_surf
    return scaled_surf
