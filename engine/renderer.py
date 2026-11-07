import pygame
from engine.textures import TEXTURES

# Pre-cache texture vertical strips for performance
TEXTURE_STRIPS = {}
for tid, tex in TEXTURES.items():
    TEXTURE_STRIPS[tid] = [tex.subsurface((x, 0, 1, 256)) for x in range(256)]
