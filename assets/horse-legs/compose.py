"""Forward kinematics + compositing for the generated legs/tail on the 2048 canvas frame."""
import math

from PIL import Image


def dirv(a):
    r = math.radians(a)
    return (-math.sin(r), math.cos(r))  # angle clockwise from straight down (y-down screen)


def place(dst, origin, img, pivot, target, angle):
    """Composite piece `img` so that its pivot lands on canvas `target`, rotated `angle` deg clockwise."""
    ox, oy = origin
    c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    # bounding box of the transformed piece on the canvas
    w, h = img.size
    corners = []
    for (u, v) in ((0, 0), (w, 0), (w, h), (0, h)):
        du, dv = u - pivot[0], v - pivot[1]
        corners.append((target[0] + du * c - dv * s, target[1] + du * s + dv * c))
    xs = [p[0] for p in corners]
    ys = [p[1] for p in corners]
    x0 = int(math.floor(min(xs) - ox)) - 1
    y0 = int(math.floor(min(ys) - oy)) - 1
    x1 = int(math.ceil(max(xs) - ox)) + 1
    y1 = int(math.ceil(max(ys) - oy)) + 1
    W, H = x1 - x0, y1 - y0
    # inverse map: output px (x, y) -> canvas (X, Y) = (x0 + ox + x + .5, ...) -> piece
    tx = x0 + ox - target[0]
    ty = y0 + oy - target[1]
    a = c
    b = s
    cc = pivot[0] + c * tx + s * ty
    d = -s
    e = c
    f = pivot[1] - s * tx + c * ty
    pm = img.convert('RGBa')
    out = pm.transform((W, H), Image.AFFINE, (a, b, cc, d, e, f), resample=Image.BICUBIC).convert('RGBA')
    dst.alpha_composite(out, (x0, y0)) if x0 >= 0 and y0 >= 0 and x1 <= dst.size[0] and y1 <= dst.size[1] else _safe_composite(dst, out, x0, y0)


def _safe_composite(dst, src, x, y):
    W, H = dst.size
    sx0, sy0 = max(0, -x), max(0, -y)
    dx0, dy0 = max(0, x), max(0, y)
    w = min(src.size[0] - sx0, W - dx0)
    h = min(src.size[1] - sy0, H - dy0)
    if w <= 0 or h <= 0:
        return
    dst.alpha_composite(src.crop((sx0, sy0, sx0 + w, sy0 + h)), (dx0, dy0))


def leg_fk(root, L1, L2, a_up, a_low, a_hoof):
    k = (root[0] + L1 * dirv(a_up)[0], root[1] + L1 * dirv(a_up)[1])
    f = (k[0] + L2 * dirv(a_low)[0], k[1] + L2 * dirv(a_low)[1])
    return k, f


def ik2(root, target, L1, L2, bend):
    """Two-bone IK. bend=+1 puts the middle joint behind (clockwise side), -1 in front."""
    dx, dy = target[0] - root[0], target[1] - root[1]
    d = min(math.hypot(dx, dy), (L1 + L2) * 0.9999)
    a_hf = math.degrees(math.atan2(-dx, dy))
    cosA = (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d)
    A = math.degrees(math.acos(max(-1, min(1, cosA))))
    a_up = a_hf + bend * A
    k = (root[0] + L1 * dirv(a_up)[0], root[1] + L1 * dirv(a_up)[1])
    a_low = math.degrees(math.atan2(-(target[0] - k[0]), target[1] - k[1]))
    return a_up, a_low
