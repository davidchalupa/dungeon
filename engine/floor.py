import numpy as np
import pygame

TEX_SIZE = 256


def surface_to_array(surf):
    """Surface -> (tex_x, tex_y, 3) uint8 array for fast sampling."""
    return np.array(pygame.surfarray.array3d(surf))


def make_sky(width, height, top=(104, 158, 235), bottom=(196, 224, 248)):
    sky = pygame.Surface((width, height))
    for y in range(height):
        t = y / max(1, height - 1)
        sky.fill(tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)),
                 (0, y, width, 1))
    pygame.draw.circle(sky, (255, 240, 180), (int(width * 0.72), int(height * 0.28)), 26)
    pygame.draw.circle(sky, (255, 250, 215), (int(width * 0.72), int(height * 0.28)), 18)
    return sky


class FloorCaster:
    """Textured floor casting, vectorized with numpy + pygame.surfarray."""

    def __init__(self, width, height, cam_height=0.5):
        self.width = width
        self.height = height
        self.horizon = height // 2
        self.cam_height = cam_height * height  # camera z, in pixels

        rows = np.arange(self.horizon + 1, height, dtype=np.float64)
        self.row_dist = self.cam_height / (rows - self.horizon)  # (rows,)
        self.t = np.linspace(0.0, 1.0, width)                    # (width,)

    def draw(self, screen, pos_x, pos_y, dir_x, dir_y, plane_x, plane_y,
             map_array, tex_arrays):
        horizon = self.horizon

        # Ray directions at the leftmost and rightmost columns
        rd0x, rd0y = dir_x - plane_x, dir_y - plane_y
        rd1x, rd1y = dir_x + plane_x, dir_y + plane_y

        # World coordinates of every floor pixel, shape (rows, width)
        dist = self.row_dist[:, None]
        fx = pos_x + dist * (rd0x + (rd1x - rd0x) * self.t[None, :])
        fy = pos_y + dist * (rd0y + (rd1y - rd0y) * self.t[None, :])

        # Texture coords: 1.0 world unit = 256 texels, wrapping
        tx = (fx * TEX_SIZE).astype(np.int64) & (TEX_SIZE - 1)
        ty = (fy * TEX_SIZE).astype(np.int64) & (TEX_SIZE - 1)

        # Which map cell each pixel lands in (clamped at the map border;
        # out-of-map pixels always get overdrawn by walls afterwards)
        map_h, map_w = map_array.shape
        cx = np.clip(fx.astype(np.int64), 0, map_w - 1)
        cy = np.clip(fy.astype(np.int64), 0, map_h - 1)
        cells = map_array[cy, cx]

        out = np.zeros((self.row_dist.shape[0], self.width, 3), dtype=np.uint8)
        for cell_value, tex_arr in tex_arrays.items():
            mask = cells == cell_value
            if not mask.any():
                continue
            out[mask] = tex_arr[tx[mask], ty[mask]]

        pix = pygame.surfarray.pixels3d(screen)   # (width, height, 3) view
        pix[:, horizon + 1:self.height, :] = np.transpose(out, (1, 0, 2))
        del pix  # release the surface lock
