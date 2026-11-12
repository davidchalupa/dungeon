import pygame
import math


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

SPIDER_ANIM_PHASES = 6

def _quad_curve_points(p0, p1, p2, segments=8):
    """Sample a quadratic Bezier (parabolic arc) between p0 and p2 with control p1."""
    pts = []
    for i in range(segments + 1):
        u = i / segments
        v = 1 - u
        x = v * v * p0[0] + 2 * v * u * p1[0] + u * u * p2[0]
        y = v * v * p0[1] + 2 * v * u * p1[1] + u * u * p2[1]
        pts.append((x, y))
    return pts


def get_cached_procedural_cave_spider(width, height, body_color, anim_phase):
    """Procedurally drawn, animated cave spider. Parabolic legs, dark palette.

    anim_phase: int in [0, SPIDER_ANIM_PHASES).
    """
    target_w = max(10, width)
    target_h = max(10, height)

    key = (target_w, target_h, body_color, anim_phase)
    if key in goblin_ghost_surface_cache:
        return goblin_ghost_surface_cache[key]

    base_size = 256
    base_surf = pygame.Surface((base_size, base_size), pygame.SRCALPHA)

    t = (anim_phase / SPIDER_ANIM_PHASES) * math.tau
    cx = base_size // 2
    cy = int(base_size * 0.60) + int(math.sin(t) * 3)  # center low so legs ground out

    # Dark, earthy palette derived from body_color (near-black when body_color is dark)
    r, g, b = body_color
    carapace = (int(r * 0.55), int(g * 0.52), int(b * 0.48), 235)
    abdomen = (int(r * 0.48), int(g * 0.44), int(b * 0.40), 240)
    marking = (int(r * 0.68), int(g * 0.60), int(b * 0.52), 190)
    leg_color = (int(r * 0.42), int(g * 0.40), int(b * 0.36), 230)
    aura_color = (r, g, b, 22)

    pygame.draw.ellipse(base_surf, aura_color, (cx - 80, cy - 70, 160, 140))

    # ---- 8 legs: 4 per side, each a pair of parabolic arcs ----
    leg_roots = [-14, -5, 5, 14]
    for side in (-1, 1):
        for i, root_x in enumerate(leg_roots):
            phase = t + i * 0.8 + (0.4 if side == 1 else 0.0)
            lift = math.sin(phase)      # stepping motion
            sway = math.cos(phase * 0.5)

            hip = (cx + side * (30 + abs(root_x) * 0.2), cy + root_x * 0.35 - 2)

            # front legs reach forward, back legs backward
            reach = (3 - i) * 10
            foot_x = cx + side * (74 + i * 5 + reach * 0.5 + int(sway * 6))
            foot_y = cy + root_x * 0.6 + 52 - int(max(0.0, lift) * 14)
            foot = (foot_x, foot_y)

            # knee: arched above the hip-foot line; height breathes with the step
            mid_x = (hip[0] + foot_x) / 2
            arch = 26 + i * 3 + int(lift * 6)
            knee = (mid_x + side * 6, min(hip[1], foot_y) - arch)

            # upper segment: hip -> knee (parabola bulging slightly outward/up)
            upper = _quad_curve_points(
                hip, (mid_x + side * 10, knee[1] - 8), knee, segments=6)
            # lower segment: knee -> foot (parabola, gentler curve)
            lower = _quad_curve_points(
                knee, ((knee[0] + foot_x) / 2, (knee[1] + foot_y) / 2 + 6), foot, segments=6)

            pygame.draw.lines(base_surf, leg_color, False, upper, 4)
            pygame.draw.lines(base_surf, leg_color, False, lower, 3)

    # ---- Abdomen (rear) with gentle pulse ----
    ab_pulse = int(math.sin(t * 2) * 2)
    ab_cx, ab_cy = cx - 30, cy + 4
    pygame.draw.ellipse(base_surf, abdomen,
                        (ab_cx - 42, ab_cy - 34 - ab_pulse, 84, 68 + ab_pulse * 2))
    # faint chevron markings
    for k in range(3):
        w = 22 - k * 6
        pygame.draw.arc(base_surf, marking,
                        (ab_cx - w, ab_cy - 18 + k * 14, w * 2, 24), 3.5, 5.9, 3)

    # ---- Cephalothorax (front, smaller) ----
    th_cx, th_cy = cx + 26, cy - 2
    pygame.draw.ellipse(base_surf, carapace, (th_cx - 26, th_cy - 22, 52, 44))

    # ---- Small mouth parts ----
    chelicerae = (int(r * 0.50), int(g * 0.47), int(b * 0.43), 225)
    pygame.draw.ellipse(base_surf, chelicerae, (th_cx + 8, th_cy + 10, 12, 14))
    pygame.draw.ellipse(base_surf, chelicerae, (th_cx + 18, th_cy + 8, 10, 12))

    # ---- 8 eyes: 2 slightly larger + 6 tiny, dim glint ----
    eye = (60, 45, 40, 255)
    glint = (190, 170, 150, 200)
    big = [(th_cx + 12, th_cy - 6), (th_cx + 20, th_cy - 4)]
    for ex, ey in big:
        pygame.draw.circle(base_surf, eye, (ex, ey), 3)
        pygame.draw.circle(base_surf, glint, (ex - 1, ey - 1), 1)
    # for ex, ey in [(-2, -10), (4, -13), (10, -15), (16, -12), (2, 0), (8, -1)]:
    #     pygame.draw.circle(base_surf, eye, (th_cx + ex, th_cy + ey), 1)

    scaled_surf = pygame.transform.smoothscale(base_surf, (target_w, target_h))
    goblin_ghost_surface_cache[key] = scaled_surf
    return scaled_surf

SLIME_ANIM_PHASES = 8

def get_cached_procedural_slime(width, height, body_color, anim_phase):
    """Procedurally drawn, disgusting spreading slime puddle with organic blobs, bubbles, and creepy eyes."""
    target_w = max(10, width)
    target_h = max(10, height)

    key = (target_w, target_h, body_color, anim_phase)
    if key in goblin_ghost_surface_cache:
        return goblin_ghost_surface_cache[key]

    base_size = 256
    base_surf = pygame.Surface((base_size, base_size), pygame.SRCALPHA)

    t = (anim_phase / SLIME_ANIM_PHASES) * math.tau
    cx = base_size // 2
    cy = int(base_size * 0.74)  # Very low profile, flattened heavily against the floor

    r, g, b = body_color
    outer_color = (r, g, b, 170)
    inner_color = (max(0, r - 35), max(0, g - 35), max(0, b - 35), 210)
    core_color = (min(255, r + 45), min(255, g + 45), min(255, b + 45), 230)

    # Organic shifting wobble values
    wobble1 = math.sin(t) * 9
    wobble2 = math.cos(t * 1.5) * 7

    # Wide spreading puddle base (flat on the ground)
    base_puddle_rect = pygame.Rect(cx - 105 + int(wobble1), cy - 35, 210 - int(wobble1 * 2), 48)
    pygame.draw.ellipse(base_surf, outer_color, base_puddle_rect)

    # Main rising ooze blob with asymmetrical wobble
    ooze_rect = pygame.Rect(cx - 70 - int(wobble2), cy - 60, 140 + int(wobble2 * 2), 58)
    pygame.draw.ellipse(base_surf, inner_color, ooze_rect)

    # Lumpy pseudopods merging into the body
    pygame.draw.circle(base_surf, inner_color, (cx - 45 + int(wobble1), cy - 30), 26)
    pygame.draw.circle(base_surf, inner_color, (cx + 40 - int(wobble1), cy - 35), 29)
    pygame.draw.circle(base_surf, core_color, (cx + int(wobble2), cy - 45), 22)

    # Disgusting internal details: dark gunk nuclei and floating air bubbles
    dark_gunk = (max(0, r - 80), max(0, g - 80), max(0, b - 80), 210)
    bubble_color = (255, 255, 255, 200)

    # Semi-digested debris / dark centers inside
    pygame.draw.circle(base_surf, dark_gunk, (cx - 18, cy - 28), 9)
    pygame.draw.circle(base_surf, dark_gunk, (cx + 22, cy - 22), 7)
    pygame.draw.circle(base_surf, dark_gunk, (cx - 4, cy - 42), 6)

    # Pustules / air bubbles trapped inside the jelly
    pygame.draw.circle(base_surf, bubble_color, (cx - 28, cy - 38), 4)
    pygame.draw.circle(base_surf, bubble_color, (cx + 14, cy - 32), 5)
    pygame.draw.circle(base_surf, bubble_color, (cx + 35, cy - 18), 3)
    pygame.draw.circle(base_surf, bubble_color, (cx - 38, cy - 18), 4)
    pygame.draw.circle(base_surf, bubble_color, (cx + 2, cy - 52), 3)

    # Creepy, sickly yellow/orange beady eyes (asymmetric, sunken, menacing)
    eye_color = (255, 210, 40, 255)
    pupil_color = (40, 15, 5, 255)

    # Left eye
    lx, ly = cx - 16, cy - 44
    pygame.draw.circle(base_surf, eye_color, (lx, ly), 5)
    pygame.draw.circle(base_surf, pupil_color, (lx - 1, ly), 2)

    # Right eye (offset position for an unsettling look)
    rx, ry = cx + 16, cy - 41
    pygame.draw.circle(base_surf, eye_color, (rx, ry), 4)
    pygame.draw.circle(base_surf, pupil_color, (rx + 1, ry), 2)

    # Wet, slimy light sheen across the top ridge
    sheen_color = (255, 255, 255, 190)
    pygame.draw.arc(base_surf, sheen_color, (cx - 55, cy - 64, 110, 28), 0.2, 2.9, 3)

    scaled_surf = pygame.transform.smoothscale(base_surf, (target_w, target_h))
    goblin_ghost_surface_cache[key] = scaled_surf
    return scaled_surf
