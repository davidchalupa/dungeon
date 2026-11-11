import math
import pygame
from ui.common import VIRTUAL_WIDTH, VIRTUAL_HEIGHT, initialize_fonts


def draw_map(surface, world_map, player_pos, dir_vec, opponents, level_name="The Dungeon"):
    font_med, font_large, font_title = initialize_fonts()

    display_title = level_name

    # Semi-transparent backdrop or solid dark container box
    map_box = pygame.Rect(80, 50, VIRTUAL_WIDTH - 160, VIRTUAL_HEIGHT - 100)
    pygame.draw.rect(surface, (15, 20, 32), map_box)
    pygame.draw.rect(surface, (100, 180, 255), map_box, 3)

    # Title & Instructions
    title_surf = font_title.render(display_title, True, (150, 220, 255))
    inst_surf = font_med.render("Press [M] or [ESC] to Close Map", True, (180, 180, 180))
    surface.blit(title_surf, (map_box.x + 20, map_box.y + 15))
    surface.blit(inst_surf, (map_box.right - inst_surf.get_width() - 20, map_box.y + 20))

    # Legend bar
    legend_y = map_box.y + 55
    legends = [
        ("Wall", (90, 90, 110)),
        ("Floor", (170, 160, 140)),
        ("Water", (50, 130, 230)),
        ("Party", (255, 60, 60))
    ]

    lx = map_box.x + 20
    for name, color in legends:
        pygame.draw.rect(surface, color, (lx, legend_y, 14, 14))
        pygame.draw.rect(surface, (200, 200, 200), (lx, legend_y, 14, 14), 1)
        lbl = font_med.render(name, True, (220, 220, 220))
        surface.blit(lbl, (lx + 18, legend_y - 2))
        lx += 95

    # Grid drawing area
    grid_rect = pygame.Rect(map_box.x + 20, map_box.y + 85, map_box.width - 40, map_box.height - 105)
    pygame.draw.rect(surface, (10, 12, 18), grid_rect)
    pygame.draw.rect(surface, (50, 70, 100), grid_rect, 1)

    rows = len(world_map)
    cols = len(world_map[0]) if rows > 0 else 0
    if cols == 0 or rows == 0:
        return

    # Compute cell dimensions (compact size)
    cell_w = grid_rect.width / cols
    cell_h = grid_rect.height / rows
    cell_size = min(cell_w, cell_h) * 0.65

    # Center the grid inside the grid_rect
    offset_x = grid_rect.x + (grid_rect.width - (cols * cell_size)) / 2
    offset_y = grid_rect.y + (grid_rect.height - (rows * cell_size)) / 2

    # Draw Map Cells (Vertically inverted so index 0 is at the bottom, matching standard Y coordinates)
    for r in range(rows):
        display_r = rows - 1 - r
        for c in range(cols):
            cell_type = world_map[display_r][c]
            if cell_type == 1:
                color = (90, 90, 110)  # Wall
            elif cell_type == 2:
                color = (50, 130, 230)  # Water
            else:
                color = (170, 160, 140)  # Floor / Open

            cell_rect = pygame.Rect(
                int(offset_x + c * cell_size),
                int(offset_y + r * cell_size),
                int(math.ceil(cell_size)),
                int(math.ceil(cell_size))
            )
            pygame.draw.rect(surface, color, cell_rect)
            pygame.draw.rect(surface, (30, 35, 45), cell_rect, 1)

    # Draw Party Directional Arrow (Red) with vertical inversion for screen space mapping
    px, py = player_pos
    p_screen_x = offset_x + px * cell_size
    p_screen_y = offset_y + (rows - py) * cell_size

    dirX, dirY = dir_vec
    mag = math.hypot(dirX, dirY)
    if mag > 0:
        dirX /= mag
        dirY /= mag

    dx = dirX
    dy = -dirY

    arrow_len = cell_size * 0.65
    arrow_width = cell_size * 0.45

    tip_x = p_screen_x + dx * arrow_len
    tip_y = p_screen_y + dy * arrow_len

    back_x = p_screen_x - dx * (arrow_len * 0.4)
    back_y = p_screen_y - dy * (arrow_len * 0.4)

    perpX = -dy
    perpY = dx

    left_x = back_x + perpX * (arrow_width * 0.5)
    left_y = back_y + perpY * (arrow_width * 0.5)

    right_x = back_x - perpX * (arrow_width * 0.5)
    right_y = back_y - perpY * (arrow_width * 0.5)

    arrow_points = [
        (int(tip_x), int(tip_y)),
        (int(left_x), int(left_y)),
        (int(right_x), int(right_y))
    ]

    pygame.draw.polygon(surface, (255, 60, 60), arrow_points)
    pygame.draw.polygon(surface, (255, 200, 200), arrow_points, 1)

    # Display internal coordinates in the lower right corner for debugging
    coord_str = f"Pos: X={px:.2f}, Y={py:.2f}"
    coord_surf = font_med.render(coord_str, True, (200, 220, 240))
    surface.blit(coord_surf, (map_box.right - coord_surf.get_width() - 20, map_box.bottom - 32))
