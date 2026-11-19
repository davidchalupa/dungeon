import pygame
import math

import engine.combat as combat


MOVE_SPEED = 0.04
ROT_SPEED = 0.035
PLAYER_RADIUS = 0.22


def handle_player_movement(posX, posY, dirX, dirY, planeX, planeY):
    """Handle player movement and rotation based on keyboard input."""
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        newX = posX + dirX * MOVE_SPEED
        newY = posY + dirY * MOVE_SPEED
        if combat.can_move_to(newX, posY, PLAYER_RADIUS):
            posX = newX
        if combat.can_move_to(posX, newY, PLAYER_RADIUS):
            posY = newY
    if keys[pygame.K_DOWN]:
        newX = posX - dirX * MOVE_SPEED
        newY = posY - dirY * MOVE_SPEED
        if combat.can_move_to(newX, posY, PLAYER_RADIUS):
            posX = newX
        if combat.can_move_to(posX, newY, PLAYER_RADIUS):
            posY = newY

    if keys[pygame.K_LEFT]:
        oldDirX = dirX
        dirX = dirX * math.cos(ROT_SPEED) - dirY * math.sin(ROT_SPEED)
        dirY = oldDirX * math.sin(ROT_SPEED) + dirY * math.cos(ROT_SPEED)
        oldPlaneX = planeX
        planeX = planeX * math.cos(ROT_SPEED) - planeY * math.sin(ROT_SPEED)
        planeY = oldPlaneX * math.sin(ROT_SPEED) + planeY * math.cos(ROT_SPEED)
    if keys[pygame.K_RIGHT]:
        oldDirX = dirX
        dirX = dirX * math.cos(-ROT_SPEED) - dirY * math.sin(-ROT_SPEED)
        dirY = oldDirX * math.sin(-ROT_SPEED) + dirY * math.cos(-ROT_SPEED)
        oldPlaneX = planeX
        planeX = planeX * math.cos(-ROT_SPEED) - planeY * math.sin(-ROT_SPEED)
        planeY = oldPlaneX * math.sin(-ROT_SPEED) + planeY * math.cos(-ROT_SPEED)
    return posX, posY, dirX, dirY, planeX, planeY
