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
