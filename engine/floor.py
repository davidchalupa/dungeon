import numpy as np
import pygame
import math

TEX_SIZE = 256
TEX_FLAT = TEX_SIZE * TEX_SIZE


def surface_to_array(surf):
    """Surface -> (tex_x, tex_y, 3) uint8 array indexed [tx, ty]."""
    return np.array(pygame.surfarray.array3d(surf))


def make_sky(width, height, top=(104, 158, 235), bottom=(196, 224, 248)):
    sky = pygame.Surface((width, height))
    for y in range(height):
        t = y / max(1, height - 1)
        sky.fill(tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)),
                 (0, y, width, 1))
    return sky

SUN_AZIMUTH = math.radians(135)   # world angle of the sun, tune to taste
SUN_HEIGHT = 0.30                  # fraction of sky band height, 0 = horizon


def draw_sun(surface, dir_x, dir_y, plane_x, plane_y):
    """Sun at a fixed world azimuth: slides across the sky as you turn.
    Self-contained: derives screen geometry from `surface`, so it works
    from any module."""
    sun_x = math.cos(SUN_AZIMUTH)
    sun_y = math.sin(SUN_AZIMUTH)

    inv_det = 1.0 / (plane_x * dir_y - dir_x * plane_y)
    transform_x = inv_det * (dir_y * sun_x - dir_x * sun_y)
    transform_y = inv_det * (-plane_y * sun_x + plane_x * sun_y)

    if transform_y <= 0.1:
        return  # behind the camera, nothing to draw

    w = surface.get_width()
    sky_band_height = surface.get_height() // 2 + 1  # same size as make_sky output

    cx = int((w / 2) * (1 + transform_x / transform_y))
    cy = int(sky_band_height * SUN_HEIGHT)

    if cx < -40 or cx > w + 40:
        return  # outside the field of view

    pygame.draw.circle(surface, (255, 240, 180), (cx, cy), 26)
    pygame.draw.circle(surface, (255, 250, 215), (cx, cy), 18)


def build_floor_luts(map_array, tex_arrays):
    """Per-level sampling tables for FloorCaster.

    tex_arrays: {cell_value: texture array OR list of frames (animated)}.
    Returns (kind_lut, stacks):
      kind_lut - (map_h, map_w) int32 grid, cell value -> texture kind index
      stacks   - one (num_kinds, 256*256, 3) uint8 table per animation frame
    """
    frames = {
        value: (arrs if isinstance(arrs, list) else [arrs])
        for value, arrs in tex_arrays.items()
    }
    values = sorted(frames)
    kind_of = {v: i for i, v in enumerate(values)}

    kind_lut = np.zeros(map_array.shape, dtype=np.int32)
    for value, kind in kind_of.items():
        kind_lut[map_array == value] = kind

    frame_count = max(len(f) for f in frames.values())
    stacks = []
    for fi in range(frame_count):
        stack = np.empty((len(values), TEX_FLAT, 3), dtype=np.uint8)
        for value, kind in kind_of.items():
            arr = frames[value][fi % len(frames[value])]
            stack[kind] = arr.reshape(TEX_FLAT, 3)
        stacks.append(stack)
    return kind_lut, stacks


class FloorCaster:
    """Textured floor casting into a low-res band surface.

    The floor is cast at (width/scale, height/scale) into self.band; the
    caller scales the band up to screen size. scale=2 -> 4x fewer pixels.
    """

    def __init__(self, render_width, render_height, scale=2):
        self.scale = scale
        self.band_w = render_width // scale
        self.horizon = render_height // 2
        self.band_h = max(1, (render_height - self.horizon - 1) // scale)

        self.cam_z = float(self.horizon)  # camera height in full-res pixels

        # Per band row: perpendicular distance of the floor strip it depicts.
        r = np.arange(self.band_h, dtype=np.float32)
        self.row_dist = self.cam_z / (r * scale + 1)   # (band_h,)

        # Per band column: interpolation factor 0..1 between leftmost and
        # rightmost ray.
        self.t = np.linspace(0.0, 1.0, self.band_w).astype(np.float32)

        self.band = pygame.Surface((self.band_w, self.band_h))

    def draw(self, pos_x, pos_y, dir_x, dir_y, plane_x, plane_y,
             kind_lut, lut_stack):
        """Update self.band with the current view. Blit the band afterwards."""
        rd0x, rd0y = dir_x - plane_x, dir_y - plane_y
        rd1x, rd1y = dir_x + plane_x, dir_y + plane_y

        # World position of every band pixel, laid out (band_w, band_h) so
        # the sampled colors can go straight into the surfarray view.
        ix = (rd0x + (rd1x - rd0x) * self.t[:, None])   # (band_w, 1)
        iy = (rd0y + (rd1y - rd0y) * self.t[:, None])
        fx = pos_x + self.row_dist[None, :] * ix       # (band_w, band_h)
        fy = pos_y + self.row_dist[None, :] * iy

        tx = (fx * TEX_SIZE).astype(np.int32) & (TEX_SIZE - 1)
        ty = (fy * TEX_SIZE).astype(np.int32) & (TEX_SIZE - 1)
        flat = tx * TEX_SIZE + ty                       # matches [tx, ty] order

        kh, kw = kind_lut.shape
        cx = np.clip(fx, 0, kw - 1).astype(np.int32)
        cy = np.clip(fy, 0, kh - 1).astype(np.int32)
        kinds = kind_lut[cy, cx]

        pix_rgb = lut_stack[kinds, flat]                # one gather, all pixels

        pix = pygame.surfarray.pixels3d(self.band)
        pix[...] = pix_rgb
        del pix  # release the surface lock
