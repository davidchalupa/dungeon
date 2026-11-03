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
