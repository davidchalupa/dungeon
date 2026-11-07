import pygame
import random
import math


# ==========================================
# PROCEDURAL TEXTURES & CACHING
# ==========================================
def create_running_bond_brick_texture():
    tex_size = 256
    surf = pygame.Surface((tex_size, tex_size))
    surf.fill((80, 80, 90))
    brick_h = 32
    brick_w = 64
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


def _tiled(surf, draw_fn):
    """Run draw_fn at 9 offsets so patterns wrap seamlessly when tiled."""
    tex_size = surf.get_width()
    for ox in (-tex_size, 0, tex_size):
        for oy in (-tex_size, 0, tex_size):
            draw_fn(ox, oy)


def create_grass_texture():
    tex_size = 256
    surf = pygame.Surface((tex_size, tex_size))
    tex_rng = random.Random(7)

    surf.fill((62, 106, 48))

    # Soft blotches for patchiness
    for _ in range(36):
        cx, cy = tex_rng.randint(0, tex_size - 1), tex_rng.randint(0, tex_size - 1)
        r = tex_rng.randint(14, 44)
        shade = tex_rng.randint(-16, 14)
        col = (max(30, 62 + shade), max(72, 106 + shade + 8), max(30, 48 + shade))
        _tiled(surf, lambda ox, oy: pygame.draw.circle(surf, col, (cx + ox, cy + oy), r))

    # Grass blades: short strokes in two greens
    for _ in range(700):
        bx, by = tex_rng.randint(0, tex_size - 1), tex_rng.randint(0, tex_size - 1)
        col = (74, 128, 56) if tex_rng.random() < 0.5 else (48, 90, 40)
        dx, bh = tex_rng.randint(-1, 1), tex_rng.randint(2, 5)
        _tiled(surf, lambda ox, oy: pygame.draw.line(
            surf, col, (bx + ox, by + oy), (bx + ox + dx, by + oy - bh)))

    # A few tiny flowers
    for _ in range(18):
        fx_, fy_ = tex_rng.randint(0, tex_size - 1), tex_rng.randint(0, tex_size - 1)
        col = tex_rng.choice([(235, 230, 120), (235, 235, 235), (200, 120, 180)])
        _tiled(surf, lambda ox, oy: pygame.draw.rect(surf, col, (fx_ + ox, fy_ + oy, 2, 2)))
    return surf


WATER_FRAME_COUNT = 4


def create_water_texture(frame=0):
    tex_size = 256
    surf = pygame.Surface((tex_size, tex_size))
    tex_rng = random.Random(99)
    shift = tex_size * frame // WATER_FRAME_COUNT  # horizontal scroll per frame

    # Depth gradient (exactly one sine period vertically, so it wraps)
    for y in range(tex_size):
        g = int(12 * math.sin(y * math.tau / tex_size))
        surf.fill((26 + g // 2, 68 + g, 138 + g), (0, y, tex_size, 1))

    # Ripple highlights; integer wave counts + horizontal shift keep the wrap seamless
    for i in range(16):
        base_y = i * tex_size // 16 + tex_rng.randint(-3, 3)
        k = tex_rng.randint(2, 5)
        amp = tex_rng.randint(2, 4)
        off = tex_rng.uniform(0, math.tau)
        col = tex_rng.choice([(98, 170, 216), (120, 190, 236), (84, 152, 206)])
        pts = [
            (x, base_y + int(amp * math.sin((x + shift) * k * math.tau / tex_size + off)))
            for x in range(0, tex_size + 4, 4)
        ]
        _tiled(surf, lambda ox, oy: pygame.draw.lines(
            surf, col, False, [(px + ox, py + oy) for (px, py) in pts], 1))
    return surf


FLOOR_TEXTURES = {
    1: create_grass_texture(),
    2: [create_water_texture(f) for f in range(WATER_FRAME_COUNT)],  # animated
}
