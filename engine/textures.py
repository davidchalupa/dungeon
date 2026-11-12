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


def create_running_bond_brick_texture_alternative(mortar=(45, 45, 55), base=(135, 135, 145),
                                                  bg=(80, 80, 90), seed=42):
    tex_size = 256
    surf = pygame.Surface((tex_size, tex_size))
    surf.fill(bg)
    brick_h = 32
    brick_w = 64
    tex_rng = random.Random(seed)

    for y in range(0, tex_size, brick_h):
        row_idx = y // brick_h
        offset = (row_idx % 2) * (brick_w // 2)
        pygame.draw.line(surf, mortar, (0, y), (tex_size, y), 3)

        for x in range(-brick_w + offset, tex_size + brick_w, brick_w):
            bx = x + 2
            by = y + 3
            bw = brick_w - 4
            bh = brick_h - 4
            c_var = tex_rng.randint(-10, 10)
            brick_color = (
                max(base[0] - 40, min(base[0] + 55, base[0] + c_var)),
                max(base[1] - 40, min(base[1] + 55, base[1] + c_var)),
                max(base[2] - 40, min(base[2] + 55, base[2] + c_var)),
            )
            pygame.draw.rect(surf, brick_color, (bx, by, bw, bh))
            pygame.draw.line(
                surf, mortar, (x + brick_w, y), (x + brick_w, y + brick_h), 3
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

    # # A few tiny flowers
    # for _ in range(18):
    #     fx_, fy_ = tex_rng.randint(0, tex_size - 1), tex_rng.randint(0, tex_size - 1)
    #     col = tex_rng.choice([(235, 230, 120), (235, 235, 235), (200, 120, 180)])
    #     _tiled(surf, lambda ox, oy: pygame.draw.rect(surf, col, (fx_ + ox, fy_ + oy, 2, 2)))
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


def create_stone_texture():
    """Courser stone-block wall: big irregular blocks, mortar gaps, weathering."""
    tex_size = 256
    surf = pygame.Surface((tex_size, tex_size))
    tex_rng = random.Random(55)

    surf.fill((70, 70, 74))  # mortar

    block_h = 42
    block_w = 84
    for y in range(0, tex_size, block_h):
        row_idx = y // block_h
        offset = (row_idx % 2) * (block_w // 2)
        for x in range(-block_w + offset, tex_size + block_w, block_w):
            c = tex_rng.randint(-14, 14)
            col = (
                max(90, min(170, 128 + c)),
                max(88, min(166, 124 + c)),
                max(86, min(162, 120 + c)),
            )
            pygame.draw.rect(surf, col, (x + 3, y + 3, block_w - 6, block_h - 6),
                             border_radius=6)
            # subtle top highlight + bottom shade for chiseled look
            pygame.draw.line(surf, (min(200, col[0] + 25),) * 3,
                             (x + 6, y + 5), (x + block_w - 6, y + 5), 2)
            pygame.draw.line(surf, (max(40, col[0] - 30),) * 3,
                             (x + 6, y + block_h - 5), (x + block_w - 6, y + block_h - 5), 2)
    # weathering speckles
    for _ in range(220):
        px, py = tex_rng.randint(0, tex_size - 1), tex_rng.randint(0, tex_size - 1)
        v = tex_rng.randint(-18, 12)
        c = surf.get_at((px, py))
        surf.set_at((px, py), (max(0, c[0] + v), max(0, c[1] + v), max(0, c[2] + v)))
    return surf


def create_shop_front_texture():
    """Plastered wall with timber frame and a wooden door: marks a shop."""
    tex_size = 256
    surf = pygame.Surface((tex_size, tex_size))
    tex_rng = random.Random(77)

    surf.fill((196, 178, 148))  # warm plaster

    # plaster mottling
    for _ in range(500):
        px, py = tex_rng.randint(0, tex_size - 1), tex_rng.randint(0, tex_size - 1)
        v = tex_rng.randint(-10, 10)
        c = surf.get_at((px, py))
        surf.set_at((px, py), (max(0, c[0] + v), max(0, c[1] + v), max(0, c[2] + v)))

    # timber frame: corner posts + horizontal beams
    timber = (94, 62, 38)
    pygame.draw.rect(surf, timber, (0, 0, 14, tex_size))            # left post
    pygame.draw.rect(surf, timber, (tex_size - 14, 0, 14, tex_size))  # right post
    pygame.draw.rect(surf, timber, (0, 0, tex_size, 16))            # top beam
    pygame.draw.rect(surf, timber, (0, tex_size - 20, tex_size, 20))  # base

    # wooden door, centered
    door = (72, 46, 26)
    dx, dy, dw, dh = 88, 66, 80, 170
    pygame.draw.rect(surf, (40, 26, 14), (dx - 4, dy - 4, dw + 8, dh + 8))  # frame
    pygame.draw.rect(surf, door, (dx, dy, dw, dh))
    for i in range(1, 4):  # vertical planks
        pygame.draw.line(surf, (52, 33, 18), (dx + i * dw // 4, dy),
                         (dx + i * dw // 4, dy + dh), 2)
    # handle
    pygame.draw.circle(surf, (200, 180, 90), (dx + dw - 14, dy + dh // 2), 5)
    # small shop sign above the door
    pygame.draw.rect(surf, (110, 78, 44), (dx + 8, dy - 30, dw - 16, 22))
    pygame.draw.rect(surf, (60, 40, 20), (dx + 8, dy - 30, dw - 16, 22), 2)
    return surf


def create_cobblestone_texture():
    """Rounded cobblestones for town streets."""
    tex_size = 256
    surf = pygame.Surface((tex_size, tex_size))
    tex_rng = random.Random(31)

    surf.fill((74, 72, 68))  # dirt between stones

    stone = 32
    for gy in range(0, tex_size, stone):
        offset = (gy // stone % 2) * (stone // 2)
        for gx in range(-stone + offset, tex_size + stone, stone):
            c = tex_rng.randint(-16, 16)
            col = (max(100, 138 + c), max(96, 132 + c), max(92, 124 + c))
            pad = tex_rng.randint(2, 4)
            rect = (gx + pad, gy + pad, stone - pad * 2, stone - pad * 2)
            pygame.draw.ellipse(surf, col, rect)
            pygame.draw.ellipse(surf, (max(70, col[0] - 30),) * 3, rect, 1)
    return surf

def create_mossy_fieldstone_texture():
    """Organic fieldstone wall: irregular rounded stones, moss, creeping vines."""
    tex_size = 256
    surf = pygame.Surface((tex_size, tex_size))
    tex_rng = random.Random(55)

    surf.fill((88, 82, 70))  # packed earth between stones

    # Irregular rounded stones in loose rows
    stone_h = 38
    for row in range(tex_size // stone_h + 1):
        y = row * stone_h
        x = -tex_rng.randint(0, 30)
        while x < tex_size:
            w = tex_rng.randint(30, 58)
            h = stone_h - tex_rng.randint(4, 10)
            c = tex_rng.randint(-16, 14)
            col = (
                max(96, min(176, 132 + c)),
                max(92, min(170, 126 + c)),
                max(86, min(160, 114 + c)),
            )
            rect = (x + 2, y + 2, w - 4, h)
            pygame.draw.ellipse(surf, col, rect)
            # top-left highlight for a lichen-kissed look
            pygame.draw.ellipse(
                surf, (min(200, col[0] + 22), min(196, col[1] + 22), min(180, col[2] + 18)),
                (rect[0] + 4, rect[1] + 3, rect[2] // 2, rect[3] // 3))
            x += w - tex_rng.randint(0, 8)  # overlap rows slightly for irregularity

    # Moss patches hugging the mortar lines
    for _ in range(22):
        mx, my = tex_rng.randint(0, tex_size - 1), tex_rng.randint(0, tex_size - 1)
        r = tex_rng.randint(2, 6)
        shade = tex_rng.randint(-6, 6)
        moss = (max(84, 104 + shade), max(104, 124 + shade), max(78, 92 + shade))
        _tiled(surf, lambda ox, oy: pygame.draw.circle(surf, moss, (mx + ox, my + oy), r))

    # Creeping vine
    vine = (58, 96, 48)
    vx = tex_rng.randint(20, tex_size - 20)
    vy = 0
    while vy < tex_size:
        step = tex_rng.randint(10, 18)
        nx = vx + tex_rng.randint(-9, 9)
        pygame.draw.line(surf, vine, (vx, vy), (nx, vy + step), 3)
        # little leaves off the vine
        pygame.draw.ellipse(surf, (74, 118, 58),
                            (nx + tex_rng.choice((-7, 5)), vy + step - 4, 7, 4))
        vx, vy = nx, vy + step

    return surf

def create_shop_wall_texture():
    """Plastered, timber-framed shop wall with a window: no door."""
    tex_size = 256
    surf = pygame.Surface((tex_size, tex_size))
    tex_rng = random.Random(78)

    surf.fill((196, 178, 148))  # same warm plaster as the door variant

    for _ in range(500):
        px, py = tex_rng.randint(0, tex_size - 1), tex_rng.randint(0, tex_size - 1)
        v = tex_rng.randint(-10, 10)
        c = surf.get_at((px, py))
        surf.set_at((px, py), (max(0, c[0] + v), max(0, c[1] + v), max(0, c[2] + v)))

    timber = (94, 62, 38)
    pygame.draw.rect(surf, timber, (0, 0, 14, tex_size))
    pygame.draw.rect(surf, timber, (tex_size - 14, 0, 14, tex_size))
    pygame.draw.rect(surf, timber, (0, 0, tex_size, 16))
    pygame.draw.rect(surf, timber, (0, tex_size - 20, tex_size, 20))

    # small-paned window
    wx, wy, ww, wh = 92, 76, 72, 64
    pygame.draw.rect(surf, timber, (wx - 5, wy - 5, ww + 10, wh + 10))
    pygame.draw.rect(surf, (52, 66, 78), (wx, wy, ww, wh))  # dim glass
    pygame.draw.line(surf, timber, (wx + ww // 2, wy), (wx + ww // 2, wy + wh), 3)
    pygame.draw.line(surf, timber, (wx, wy + wh // 2), (wx + ww, wy + wh // 2), 3)
    # faint glass glint
    pygame.draw.line(surf, (120, 140, 155), (wx + 8, wy + wh - 10),
                     (wx + 22, wy + 8), 2)
    return surf


def create_mossy_fieldstone_door_texture():
    """Mossy fieldstone wall with a recessed wooden entrance: town doorways."""
    tex_size = 256
    surf = pygame.Surface((tex_size, tex_size))
    tex_rng = random.Random(56)

    surf.fill((88, 82, 70))

    # Same fieldstone base as texture 3
    stone_h = 38
    for row in range(tex_size // stone_h + 1):
        y = row * stone_h
        x = -tex_rng.randint(0, 30)
        while x < tex_size:
            w = tex_rng.randint(30, 58)
            h = stone_h - tex_rng.randint(4, 10)
            c = tex_rng.randint(-16, 14)
            col = (
                max(96, min(176, 132 + c)),
                max(92, min(170, 126 + c)),
                max(86, min(160, 114 + c)),
            )
            rect = (x + 2, y + 2, w - 4, h)
            pygame.draw.ellipse(surf, col, rect)
            pygame.draw.ellipse(
                surf, (min(200, col[0] + 22), min(196, col[1] + 22), min(180, col[2] + 18)),
                (rect[0] + 4, rect[1] + 3, rect[2] // 2, rect[3] // 3))
            x += w - tex_rng.randint(0, 8)

    # Subtle moss
    for _ in range(22):
        mx, my = tex_rng.randint(0, tex_size - 1), tex_rng.randint(0, tex_size - 1)
        r = tex_rng.randint(2, 6)
        shade = tex_rng.randint(-6, 6)
        moss = (max(84, 104 + shade), max(104, 124 + shade), max(78, 92 + shade))
        _tiled(surf, lambda ox, oy: pygame.draw.circle(surf, moss, (mx + ox, my + oy), r))

    # Recessed arched wooden door, centered
    dx, dy, dw, dh = 84, 70, 88, 176
    # dark recess around the door so it reads as inset
    pygame.draw.rect(surf, (52, 48, 42), (dx - 10, dy - 10, dw + 20, dh + 10))
    # arch: stacked shrinking slabs + rounded top
    pygame.draw.rect(surf, (70, 46, 26), (dx, dy + 24, dw, dh - 24))
    pygame.draw.ellipse(surf, (70, 46, 26), (dx, dy - 10, dw, 70))
    pygame.draw.rect(surf, (52, 34, 18), (dx, dy + 24, dw, dh - 24), 3)
    # vertical planks
    for i in range(1, 4):
        pygame.draw.line(surf, (54, 36, 20), (dx + i * dw // 4, dy + 14),
                         (dx + i * dw // 4, dy + dh), 2)
    # iron hinges and handle
    pygame.draw.rect(surf, (90, 90, 96), (dx + 4, dy + 40, 12, 5))
    pygame.draw.rect(surf, (90, 90, 96), (dx + dw - 16, dy + 40, 12, 5))
    pygame.draw.circle(surf, (140, 130, 100), (dx + dw - 14, dy + 110), 5)
    # stone step
    pygame.draw.rect(surf, (120, 116, 108), (dx - 14, dy + dh - 4, dw + 28, 14))
    return surf


TEXTURES = {
    1: create_running_bond_brick_texture(),
    2: create_organic_texture(),
    3: create_mossy_fieldstone_texture(),
    4: create_shop_front_texture(),
    5: create_running_bond_brick_texture_alternative(),
    6: create_shop_wall_texture(),
    7: create_mossy_fieldstone_door_texture(),
}

FLOOR_TEXTURES = {
    1: create_grass_texture(),
    2: [create_water_texture(f) for f in range(WATER_FRAME_COUNT)],  # animated
    3: create_cobblestone_texture(),
}
