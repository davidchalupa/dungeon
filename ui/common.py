import pygame

VIRTUAL_WIDTH, VIRTUAL_HEIGHT = 840, 740

font_med = None
font_large = None
font_title = None

# Load Fonts for UI
def initialize_fonts():
    global font_med, font_large, font_title
    font_med = pygame.font.SysFont(None, 20)
    font_large = pygame.font.SysFont(None, 24)
    font_title = pygame.font.SysFont(None, 28, bold=True)
    return font_med, font_large, font_title


def get_fonts():
    return font_med, font_large, font_title


def get_virtual_mouse_pos(surface):
    """Maps raw window mouse position to virtual (840x740) surface coordinates."""
    raw_x, raw_y = pygame.mouse.get_pos()

    # Get the actual current window size from pygame display or surface
    win_w, win_h = pygame.display.get_surface().get_size()

    virtual_aspect = VIRTUAL_WIDTH / VIRTUAL_HEIGHT
    window_aspect = win_w / win_h if win_h > 0 else virtual_aspect

    if window_aspect > virtual_aspect:
        scaled_h = win_h
        scaled_w = int(scaled_h * virtual_aspect)
        scale_x = (win_w - scaled_w) // 2
        scale_y = 0
    else:
        scaled_w = win_w
        scaled_h = int(scaled_w / virtual_aspect)
        scale_x = 0
        scale_y = (win_h - scaled_h) // 2

    # Prevent division by zero
    if scaled_w <= 0 or scaled_h <= 0:
        return pygame.mouse.get_pos()

    # Scale raw coordinates relative to the letterboxed game surface display rect
    virt_x = int((raw_x - scale_x) * (VIRTUAL_WIDTH / scaled_w))
    virt_y = int((raw_y - scale_y) * (VIRTUAL_HEIGHT / scaled_h))

    return (virt_x, virt_y)
