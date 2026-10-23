"""Beveled-block renderer (pycairo) + paper texture borrowed from body.png."""
import math
import os

import cairo
import numpy as np
from PIL import Image, ImageFilter

from geom import dedupe, edge_normal, ensure_cw, lerp, offset_poly

OL = 15.0  # outline width, canvas px (body outline is ~14px + soft edge)
OUTLINE = (13, 8, 5)

BODY_PNG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'horse-upper', 'pieces', 'body.png')
TEX_BOX = (480, 130, 1150, 560)  # clean face region of body.png (body-local px)


def c255(c):
    return tuple(v / 255.0 for v in c)


def dir_lerp(n, spec):
    """Interpolate a value keyed by outward-normal direction: spec has up/left/right/down."""
    ang = math.degrees(math.atan2(n[1], n[0]))  # 0 right, 90 down, -90 up, +-180 left
    keys = [(-180, 'left'), (-90, 'up'), (0, 'right'), (90, 'down'), (180, 'left')]
    for (a0, k0), (a1, k1) in zip(keys, keys[1:]):
        if a0 <= ang <= a1:
            t = (ang - a0) / (a1 - a0)
            # keep the lit 'up' colour a little broader than linear
            v0, v1 = spec[k0], spec[k1]
            if isinstance(v0, tuple):
                return tuple(lerp(v0[i], v1[i], t) for i in range(len(v0)))
            return lerp(v0, v1, t)
    return spec['left']


def path_poly(ctx, poly):
    ctx.new_path()
    ctx.move_to(*poly[0])
    for p in poly[1:]:
        ctx.line_to(*p)
    ctx.close_path()


def fill_poly(ctx, poly, col, alpha=1.0, seam=0.0):
    path_poly(ctx, poly)
    ctx.set_source_rgba(*c255(col), alpha)
    if seam > 0:
        ctx.fill_preserve()
        ctx.set_line_width(seam)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke()
    else:
        ctx.fill()


def outline(ctx, poly, width=OL):
    path_poly(ctx, poly)
    ctx.set_source_rgb(*c255(OUTLINE))
    ctx.set_line_width(2 * width)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke_preserve()
    ctx.fill()


def _axis_aligned(n, tol=20.0):
    ang = math.degrees(math.atan2(n[1], n[0])) % 90.0
    return ang < tol or ang > 90.0 - tol


def bevel_block(ctx, P, style, draw_outline=True):
    """P: polygon on the inner edge of the outline. style: dict with
    bw (bevel width by direction), col (bevel colour by direction), face, hl (face highlight
    width by direction), hl_col, rim (dark rim width by direction), rim_k."""
    P = ensure_cw(dedupe(P))
    n = len(P)
    normals = [edge_normal(P[i], P[(i + 1) % n]) for i in range(n)]
    if draw_outline:
        outline(ctx, P)
    bw = [dir_lerp(nm, style['bw']) for nm in normals]
    Q = offset_poly(P, bw)
    # base under facets (hides AA seams)
    fill_poly(ctx, P, style['col']['right'])
    for i in range(n):
        j = (i + 1) % n
        if bw[i] <= 0.01:
            continue
        col = dir_lerp(normals[i], style['col'])
        fill_poly(ctx, [P[i], P[j], Q[j], Q[i]], col, seam=1.0)
    rim = style.get('rim')
    if rim:
        rw = [dir_lerp(nm, rim) for nm in normals]
        P2 = offset_poly(P, rw)
        for i in range(n):
            j = (i + 1) % n
            if rw[i] <= 0.3:
                continue
            col = dir_lerp(normals[i], style['col'])
            k = style.get('rim_k', 0.82)
            fill_poly(ctx, [P[i], P[j], P2[j], P2[i]], tuple(c * k for c in col), seam=0.8)
    hl = style.get('hl')
    if hl:
        # face highlight stripes only on edges that clearly face one direction (no tapered tails round chamfers)
        Qd = dedupe(Q)
        hw = [dir_lerp(nm, hl) if _axis_aligned(nm) else 0.0
              for nm in (edge_normal(Qd[i], Qd[(i + 1) % len(Qd)]) for i in range(len(Qd)))]
        Q2 = offset_poly(Qd, hw)
        fill_poly(ctx, Q, style['hl_col'])
        fill_poly(ctx, Q2, style['face'])
    else:
        fill_poly(ctx, Q, style['face'])
    return P, Q


class Canvas:
    """A piece surface; local coordinates have the pivot at (0, 0)."""

    def __init__(self, x0, y0, x1, y1, pad=6):
        self.ox = math.floor(x0) - pad
        self.oy = math.floor(y0) - pad
        self.w = int(math.ceil(x1) - self.ox + pad)
        self.h = int(math.ceil(y1) - self.oy + pad)
        self.surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.w, self.h)
        self.ctx = cairo.Context(self.surf)
        self.ctx.set_antialias(cairo.ANTIALIAS_BEST)
        self.ctx.translate(-self.ox, -self.oy)

    @property
    def pivot(self):
        return (-self.ox, -self.oy)

    def rgba(self):
        buf = np.ndarray((self.h, self.w, 4), np.uint8, self.surf.get_data(), strides=(self.surf.get_stride(), 4, 1)).copy()
        b, g, r, a = [buf[:, :, i].astype(np.float32) for i in range(4)]
        out = np.zeros((self.h, self.w, 4), np.float32)
        nz = a > 0
        for i, ch in enumerate((r, g, b)):
            out[:, :, i][nz] = ch[nz] * 255.0 / a[nz]
        out[:, :, 3] = a
        return out


_TEX = None
TEX_FACE_L = 168.0  # mean luminance of the body face the texture was sampled from


def body_texture():
    """RGB high-pass of the body's paper/fibre texture (zero mean, body px units)."""
    global _TEX
    if _TEX is None:
        import cv2
        im = np.asarray(Image.open(BODY_PNG).convert('RGB').crop(TEX_BOX), np.float32)
        low = cv2.GaussianBlur(im, (0, 0), 30)
        D = im - low
        D = np.clip(D, -28, 28)
        _TEX = D - D.reshape(-1, 3).mean(0)
    return _TEX


def tex_field(h, w, seed, rotate=True):
    T = body_texture()
    if rotate:
        T = T.transpose(1, 0, 2)  # fibres run along the leg
    rng = np.random.default_rng(seed)
    big = np.concatenate([np.concatenate([T, T[:, ::-1]], 1), np.concatenate([T[::-1], T[::-1, ::-1]], 1)], 0)
    reps_y = h // big.shape[0] + 2
    reps_x = w // big.shape[1] + 2
    big = np.tile(big, (reps_y, reps_x, 1))
    oy = int(rng.integers(0, T.shape[0]))
    ox = int(rng.integers(0, T.shape[1]))
    return big[oy:oy + h, ox:ox + w]


def finish(rgba, seed, tex_k=1.0, dark_tex_k=0.6, soften=0.6, tint=None, gain=None):
    """Transfer the body's paper texture onto the painted (non-outline) pixels; soften edges slightly."""
    h, w = rgba.shape[:2]
    T = tex_field(h, w, seed)
    rgb = rgba[:, :, :3]
    if gain is not None:
        # colour-match mid tones only; leave the cream highlights (L > ~215) untouched
        L0 = rgb.mean(2)
        g_w = 1.0 - np.clip((L0 - 190.0) / 25.0, 0, 1)
        g = np.asarray(gain, np.float32)[None, None, :]
        rgb = rgb * (1.0 + (g - 1.0) * g_w[:, :, None])
    L = rgb.mean(2)
    wt = np.clip((L - 25) / 60.0, 0, 1)  # outline gets nothing
    k = np.where(L > 110, tex_k, dark_tex_k) * np.clip(L / TEX_FACE_L, 0, 1.2)
    rgb = rgb + T * (k * wt)[:, :, None]
    if tint is not None:
        rgb = rgb * np.asarray(tint, np.float32)[None, None, :] * wt[:, :, None] + rgb * (1 - wt[:, :, None])
    out = np.concatenate([np.clip(rgb, 0, 255), rgba[:, :, 3:4]], 2)
    im = Image.fromarray(out.round().astype(np.uint8), 'RGBA')
    if soften > 0:
        r, g, b, a = im.split()
        a = a.filter(ImageFilter.GaussianBlur(soften))
        rgbim = Image.merge('RGB', (r, g, b)).filter(ImageFilter.GaussianBlur(soften * 0.6))
        im = Image.merge('RGBA', (*rgbim.split(), a))
    return im
