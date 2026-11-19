import math

from assets import cell_types
import engine.combat as combat


def cast_rays(posX, posY, dirX, dirY, planeX, planeY, WORLD_MAP, RENDER_WIDTH):
    """Perform raycasting to determine wall positions for rendering."""
    ray_cache = []
    for x in range(RENDER_WIDTH):
        cameraX = 2 * x / RENDER_WIDTH - 1
        rayDirX = dirX + planeX * cameraX
        rayDirY = dirY + planeY * cameraX

        mapX = int(posX)
        mapY = int(posY)

        deltaDistX = abs(1 / rayDirX) if rayDirX != 0 else 1e30
        deltaDistY = abs(1 / rayDirY) if rayDirY != 0 else 1e30

        hit = 0  # 0 = searching, 1 = solid wall hit (1), 2 = open sea / horizon
        side = 0

        if rayDirX < 0:
            stepX = -1
            sideDistX = (posX - mapX) * deltaDistX
        else:
            stepX = 1
            sideDistX = (mapX + 1.0 - posX) * deltaDistX

        if rayDirY < 0:
            stepY = -1
            sideDistY = (posY - mapY) * deltaDistY
        else:
            stepY = 1
            sideDistY = (mapY + 1.0 - posY) * deltaDistY

        while hit == 0:
            if sideDistX < sideDistY:
                sideDistX += deltaDistX
                mapX += stepX
                side = 0
            else:
                sideDistY += deltaDistY
                mapY += stepY
                side = 1

            # Check map boundaries
            if mapX < 0 or mapX >= len(WORLD_MAP[0]) or mapY < 0 or mapY >= len(WORLD_MAP):
                hit = 2
                break

            cell_type = WORLD_MAP[mapY][mapX]
            if cell_types.is_wall(cell_type):
                hit = 1  # Solid wall (brick, stone, or shop front)
            elif cell_type == 2:
                pass  # Water: ray passes through
            elif combat.is_wall(mapX, mapY):
                hit = 1

        if hit == 1:
            if side == 0:
                perpWallDist = (mapX - posX + (1 - stepX) / 2) / rayDirX
                wallX = posY + perpWallDist * rayDirY
            else:
                perpWallDist = (mapY - posY + (1 - stepY) / 2) / rayDirY
                wallX = posX + perpWallDist * rayDirX

            wallX -= math.floor(wallX)
        else:
            perpWallDist = float('inf')  # Infinite distance so sprites over water render properly
            wallX = 0

        ray_cache.append({
            "hit": hit,
            "perpWallDist": perpWallDist,
            "side": side,
            "wallX": wallX,
            "rayDirX": rayDirX,
            "rayDirY": rayDirY,
            "cell_type": cell_type if hit == 1 else 0,
        })
    return ray_cache
