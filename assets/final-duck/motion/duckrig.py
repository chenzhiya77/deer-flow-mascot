"""Final-duck rig: poses the final-duck pieces (../manifest.json) from an opening-style duck pose and renders
them into a premultiplied float32 layer at any scale, the same way the horse rigs do. (duckrig.py, not rig.py:
the horse neck rig is imported as `rig` next to it.)

Conventions: duck px = the 1856x1280 final-duck canvas (continuous, y down); world = the caller's canvas
(e.g. the 2048 horse canvas); angles in degrees, + = clockwise on screen. The pose dict carries the opening's
duckPose fields (rot, head, wingN, wingF, spread, legs, legPhase, eye, lx, ly, beak, vx, vy, sit, sx, sy, T)
plus where the duck goes: x, y = world position of the anchor (sole centre standing, box bottom seated),
k = world px per duck px, ground = world y the boots stand on (None: no ground).

The duck is a frontal box without a separate head, so the opening's pose is mapped onto it:
- head tilt: the duck leans 0.2 x head about the box bottom and the face (eyes, beak) slides down,
- wings: the round hands swing on circles around two shoulder points (wingN -> hand_1, wingF -> hand_0),
- legs: the boots stay upright under the box; on the ground they cannot sink (they slide up behind the box)
  and when a box corner rises they come along, so a boot never hangs loose under the box,
- beak: the lower beak drops BEAK_OPEN px x beak over a drawn mouth cavity,
- bandana tail: bent along a chain spine (../../horse-legs/tailrig.py) by the opening's scarf-tail wind.
Seated on the horse, the duck is split at its middle: render(part='far') goes behind the horse (right boot,
right hand, right half of the box), render(part='near') in front of it (left boot, left hand, left half).

Self-check: python duckrig.py  (rest pose vs ../duck-final-1856x1280.png; far + near halves vs the whole)
"""
import json
import math
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.dirname(HERE)                                   # assets/final-duck
sys.path.insert(0, os.path.join(os.path.dirname(PACK), 'horse-legs'))
import tailrig as TR  # noqa: E402

with open(os.path.join(PACK, 'manifest.json'), encoding='utf-8') as _f:
    MAN = json.load(_f)
LAY = {L['name']: L for L in MAN['layers']}
CW, CH = MAN['canvas']['w'], MAN['canvas']['h']

# ---------------------------------------------------------------- rig constants (duck px unless noted)
FOOT = (939.0, 1277.0)       # standing anchor: between the boot soles, on the ground
SIT = (939.0, 1132.5)        # seated anchor: middle of the box bottom (also the lean pivot)
SPLIT_X, SPLIT_PAD = 939.0, 16.0   # far / near split line when seated; both halves overlap by 2 x pad
SIT_SQUEEZE = 0.9            # box width x this when seated (astride the saddle)
U = 6.5                      # duck px per opening unit: 5.70 px/unit on the horse canvas / 0.877 riding scale
LEAN_HEAD = 0.2              # body lean per deg of head tilt
EYE_SHIFT = (14.0, 10.0, 0.9)     # eyes: px per lx, per ly, per deg of head
BEAK_SHIFT = (6.0, 4.0, 0.9)      # beak: same
BEAK_OPEN = 70.0             # lower beak drop at beak = 1
SHOULDER = ((552.0, 780.0), (1328.0, 780.0))   # hand_0 / hand_1 swing centres (box sides)
HAND_R, HAND_SPREAD = 206.0, 24.0               # swing radius, + spread
HAND_A0, HAND_GAIN = 42.0, 0.68                 # hand angle at wing = 4 (rest), deg per wing deg
BOX_X = (552.0, 1328.0)      # box sides
BOX_BOTTOM = 1132.5
BOOT_TUCK = 4.0              # px a boot top stays hidden behind the box bottom (as drawn)
TAIL_PIVOT = (265.0, 300.0)  # bandana tail piece px under the knot
TAIL_CAP = (-20.0, 115.0)    # world angle range of the tail links (deg clockwise from straight down)
TAIL_LINKS = 7
EYE_MAP = dict(open='normal', blink='normal', happy='miyanxiao', shock='zhuangsha', determined='renzheng',
               squeeze='hengmiyanxiao', sparkle='daimeng')   # opening eye -> final-duck eye state


def lerp(a, b, t):
    return a + (b - a) * t


def clamp(x, a, b):
    return max(a, min(b, x))


def T3(tx, ty):
    return np.array([[1, 0, tx], [0, 1, ty], [0, 0, 1.]])


def S3(sx, sy):
    return np.diag([sx, sy, 1.])


def Rot3(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.]])


HALF = T3(0.5, 0.5)      # pixel index -> continuous coordinate
UNHALF = T3(-0.5, -0.5)


def apply(M, x, y):
    return M[0, 0] * x + M[0, 1] * y + M[0, 2], M[1, 0] * x + M[1, 1] * y + M[1, 2]


def premul(u8):
    a = u8.astype(np.float32) / 255
    return np.concatenate([a[..., :3] * a[..., 3:4], a[..., 3:4]], 2)


def load(rel):
    return np.asarray(Image.open(os.path.join(PACK, rel)).convert('RGBA'))


def put(layer, src, A, keep=None):
    """Composite premultiplied src into layer through A (3x3: src index -> layer index), bbox-limited.
    keep: optional layer-sized map the warped src is multiplied by first."""
    h, w = src.shape[:2]
    c = A @ np.array([[-0.5, w - 0.5, w - 0.5, -0.5], [-0.5, -0.5, h - 0.5, h - 0.5], [1, 1, 1, 1.]])
    x0, y0 = max(0, int(math.floor(c[0].min())) - 1), max(0, int(math.floor(c[1].min())) - 1)
    x1, y1 = min(layer.shape[1], int(math.ceil(c[0].max())) + 2), min(layer.shape[0], int(math.ceil(c[1].max())) + 2)
    if x1 <= x0 or y1 <= y0:
        return
    out = cv2.warpAffine(src, (T3(-x0, -y0) @ A)[:2], (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    if keep is not None:
        out *= keep[y0:y1, x0:x1, None]
    sub = layer[y0:y1, x0:x1]
    sub *= 1 - out[..., 3:4]
    sub += out


def rect(name):
    r = LAY[name]['rect']
    return r['x'], r['y'], r['w'], r['h']


def piece_rgba(name):
    """Piece at its own resolution, the ahoge cut by its hat-brim clipPolygon (given in rect px)."""
    L = LAY[name]
    im = load(L['file'])
    if 'clipPolygon' in L:
        poly = L['clipPolygon']
        poly = json.loads(poly) if isinstance(poly, str) else poly
        h, w = im.shape[:2]
        fx, fy = w / L['rect']['w'], h / L['rect']['h']
        mk = Image.new('L', (w, h), 0)
        ImageDraw.Draw(mk).polygon([(x * fx, y * fy) for x, y in poly], fill=255)
        im = im.copy()
        im[..., 3] = (im[..., 3].astype(np.uint16) * np.asarray(mk) // 255).astype(np.uint8)
    return im


def shaft(name):
    """Boot shaft top centre (duck px) and half width, from the top rows of the piece."""
    x, y, w, h = rect(name)
    a = load(LAY[name]['file'])[..., 3] > 128
    sx = w / a.shape[1]
    cols = np.nonzero(a[: max(2, a.shape[0] // 10)].any(0))[0]
    return (x + (cols.min() + cols.max() + 1) / 2 * sx, y), (cols.max() + 1 - cols.min()) / 2 * sx


# ---------------------------------------------------------------- mouth cavity
INK = (13, 8, 5)


def _contour(name, which):
    x0, y0, w, h = rect(name)
    im = Image.fromarray(load(LAY[name]['file'])).resize((round(w), round(h)), Image.LANCZOS)
    a = np.asarray(im)[..., 3] > 128
    out = {}
    for x in range(a.shape[1]):
        ys = np.nonzero(a[:, x])[0]
        if len(ys):
            out[x + round(x0)] = (ys.max() if which == 'bottom' else ys.min()) + round(y0)
    return out


UP_B = _contour('beak_upper', 'bottom')   # upper beak underside, per duck px column
LO_T = _contour('beak_lower', 'top')      # lower beak top edge


def cavity(dy):
    """Dark mouth between the upper beak's underside and the lower beak dropped by dy px:
    (premultiplied float32 image, (x, y) duck px of its top-left), or None when closed."""
    if dy < 1:
        return None
    xs = sorted(set(UP_B) & set(LO_T))
    x0, x1 = xs[0] + 14, xs[-1] - 14
    top = [(x, UP_B[x] - 10) for x in range(x0, x1 + 1, 4)]
    bot = [(x, LO_T[x] + dy + 10) for x in range(x1, x0 - 1, -4)]
    bx, by = x0 - 12, min(p[1] for p in top) - 12
    bw, bh = x1 - x0 + 24, max(p[1] for p in bot) + 12 - by
    loc = lambda pts: [(x - bx, y - by) for x, y in pts]  # noqa: E731
    poly = loc(top + bot)
    mk = Image.new('L', (bw, bh), 0)
    ImageDraw.Draw(mk).polygon(poly, fill=255)
    mk = np.asarray(mk.filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255
    # fill: dark maroon, a touch lighter toward the bottom; tongue at the bottom middle
    ytop, ybot = min(p[1] for p in top) - by, max(p[1] for p in bot) - by
    g = np.clip((np.arange(bh, dtype=np.float32)[:, None] - ytop) / max(1, ybot - ytop), 0, 1)[..., None]
    rgb = np.array([52, 16, 20], np.float32) * (1 - g) + np.array([104, 34, 40], np.float32) * g
    fill = Image.fromarray(np.concatenate([np.broadcast_to(rgb, (bh, bw, 3)), np.full((bh, bw, 1), 255, np.float32)],
                                          2).astype(np.uint8), 'RGBA')
    cx = (x0 + x1) / 2 - bx
    tw, tb, th = (x1 - x0) * 0.30, LO_T[int((x0 + x1) / 2)] + dy + 10 - by, min(0.62 * dy + 8, 46)
    tongue = Image.new('RGBA', (bw, bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(tongue)
    d.ellipse([cx - tw, tb - th, cx + tw, tb + th * 0.9], fill=(186, 76, 80, 255))
    d.ellipse([cx - tw * 0.55, tb - th * 0.82, cx + tw * 0.05, tb - th * 0.45], fill=(222, 128, 124, 200))
    fill.alpha_composite(tongue.filter(ImageFilter.GaussianBlur(1.0)))
    f = np.asarray(fill, np.float32) / 255
    # inner shadow under the upper beak
    sh = Image.new('L', (bw, bh), 0)
    ImageDraw.Draw(sh).line(loc(top), fill=200, width=22)
    f[..., :3] *= 1 - np.asarray(sh.filter(ImageFilter.GaussianBlur(7)), np.float32)[..., None] / 255 * 0.55
    # ink rim (only the side ends show: the beaks cover top and bottom)
    rim = Image.new('L', (bw, bh), 0)
    ImageDraw.Draw(rim).polygon(poly, outline=255, width=7)
    ra = np.asarray(rim.filter(ImageFilter.GaussianBlur(0.8)), np.float32)[..., None] / 255
    rgb = f[..., :3] * (1 - ra) + np.array(INK, np.float32) / 255 * ra
    a = mk[..., None]
    return np.concatenate([rgb * a, a], 2).astype(np.float32), (bx, by)


# ---------------------------------------------------------------- bandana tail
_TX, _TY, _TW, _TH = rect('bandana_tail')
_TAIL_U8 = load(LAY['bandana_tail']['file'])
TS = _TW / _TAIL_U8.shape[1]                      # tail piece px -> duck px
TAIL_AXIS = math.degrees(math.atan2(265 - 59, 1013 - 300))   # drawn rest axis (tip at piece px (59, 1013))
TAIL = TR.TailRig(_TAIL_U8, TAIL_PIVOT, TAIL_AXIS, 0.0)
TAIL_TARGET = (_TX / TS + TAIL_PIVOT[0], _TY / TS + TAIL_PIVOT[1])   # pivot in tail-rig units (duck px / TS)


def tail_dev(p, lean):
    """Opening scarf tail (Duck.tsx scarfTail): wind = -velocity; t = speed / 650 blends the drawn hang into
    the wind direction with a faster, wider wave. Returns per-link deviations from the drawn rest (deg),
    body-local (the duck's lean is taken out, so the tail keeps its world direction), world angle capped."""
    wx, wy = -p.get('vx', 0.0), -p.get('vy', 0.0)
    aw = math.degrees(math.atan2(wy, wx))
    if aw < 45:
        aw += 360
    t = clamp(math.hypot(wx, wy) / 650, 0, 1)
    amp, fr, T = lerp(4, 16, t), lerp(1.2, 7.5, t), p.get('T', 0.0)
    out = []
    for i in range(TAIL_LINKS):
        world = TAIL_AXIS + t * (aw - 100) - 3 * t * i + amp * math.sin(2 * math.pi * fr * T - 0.95 * i) * (0.35 + 0.12 * i)
        out.append(clamp(world, *TAIL_CAP) - lean - TAIL_AXIS)
    return out


# ---------------------------------------------------------------- pose -> transforms
def body_matrix(p):
    """Duck px -> world for the box and everything on it; also (kx, ky, lean)."""
    sit = p.get('sit', 0.0)
    kx = p['k'] * p.get('sx', 1.0) * lerp(1, SIT_SQUEEZE, sit)
    ky = p['k'] * p.get('sy', 1.0)
    ax, ay = lerp(FOOT[0], SIT[0], sit), lerp(FOOT[1], SIT[1], sit)
    lean = p.get('rot', 0.0) + LEAN_HEAD * p.get('head', 0.0)
    hx, hy = kx * (SIT[0] - ax), ky * (SIT[1] - ay)   # lean pivot relative to the anchor (world)
    M = T3(p['x'], p['y']) @ T3(hx, hy) @ Rot3(lean) @ T3(-hx, -hy) @ S3(kx, ky) @ T3(-ax, -ay)
    return M, kx, ky, lean


def hand_center(i, wing, spread):
    sx, sy = SHOULDER[i]
    r, th = HAND_R + HAND_SPREAD * spread, math.radians(HAND_A0 + (wing - 4) * HAND_GAIN)
    return (sx - r * math.sin(th) if i == 0 else sx + r * math.sin(th)), sy + r * math.cos(th)


SHAFT = {n: shaft(n) for n in ('boot_l', 'boot_r')}


def boot_offsets(name, p):
    """Mode offsets (duck px): dx, dy (+ down), tilt (deg), grounded (ground and box rules apply)."""
    near = name == 'boot_l'
    side = -1.0 if near else 1.0          # toe direction: boot_l toe left, boot_r toe right
    mode = p.get('legs', 'stand')
    if mode == 'run':                      # opening legGeom 'run': near phase ph, far ph + pi
        ph = p.get('legPhase', 0.0) * 2 * math.pi + (0 if near else math.pi)
        if math.sin(ph) >= 0:              # stance
            return (16 * math.cos(ph) + 2) * U, 0.0, 0.0, True
        return (16 * math.cos(ph) + 2) * U, 13 * math.sin(ph) * U, side * 0.45 * (38 * -math.sin(ph) - 12), True
    if mode == 'tuck':
        return 6 * U, -9 * U, side * 12, False
    if mode == 'dangle':
        return side * 10, 3 * U, side * 14, False
    if mode == 'sit':
        return 0.0, 0.0, 0.0, False
    return 0.0, 0.0, 0.0, True             # stand / crouch


def boot_matrix(name, p, M, kx, ky):
    (ax, ay), hw = SHAFT[name]
    dx, dy, tilt, grounded = boot_offsets(name, p)
    Px, Py = apply(M, ax, ay)
    Px, Py = Px + kx * dx, Py + ky * dy
    B = T3(Px, Py) @ Rot3(tilt) @ S3(kx, ky) @ T3(-ax, -ay)
    if grounded:
        x, y, w, h = rect(name)
        low = max(apply(B, cx, cy)[1] for cx, cy in ((x, y + h), (x + w, y + h)))
        g = p.get('ground')
        up = max(0.0, low - g) if g is not None else 0.0          # cannot sink into the ground
        # the shaft top stays tucked behind the box bottom: follow a rising box corner
        e0, e1 = clamp(ax + dx - hw, *BOX_X), clamp(ax + dx + hw, *BOX_X)
        edge = min(apply(M, e, BOX_BOTTOM)[1] for e in (e0, e1)) - ky * BOOT_TUCK
        up = max(up, Py - edge)
        B = T3(0, -up) @ B
    return B


class Duck:
    """Prescaled-piece cache + render(view_matrix, pose, size, part)."""

    def __init__(self):
        self._src, self._small = {}, {}

    def src(self, key):
        if key not in self._src:
            if isinstance(key, tuple):           # ('eye', state, i)
                e = MAN['eyeStates'][key[1]]['eye_%d' % key[2]]
                self._src[key] = premul(load(e['file']))
            else:
                self._src[key] = premul(piece_rgba(key))
        return self._src[key]

    def small(self, key, sw, sh):
        k = (key, sw, sh)
        if k not in self._small:
            if len(self._small) >= 400:        # bounded: a moving camera / squash makes new sizes every frame
                self._small.clear()
            s = self.src(key)
            interp = cv2.INTER_AREA if sw < s.shape[1] else cv2.INTER_CUBIC
            self._small[k] = np.clip(cv2.resize(s, (sw, sh), interpolation=interp), 0, 1)
        return self._small[k]

    def elements(self, p):
        """[(kind, key or image, rect (x, y, w, h) duck px, matrix duck px -> world, group)] back to front."""
        M, kx, ky, lean = body_matrix(p)
        lx, ly, hd = p.get('lx', 0.0), p.get('ly', 0.0), p.get('head', 0.0)
        Fe = T3(EYE_SHIFT[0] * lx, EYE_SHIFT[1] * ly + EYE_SHIFT[2] * hd)
        Fb = T3(BEAK_SHIFT[0] * lx, BEAK_SHIFT[1] * ly + BEAK_SHIFT[2] * hd)
        eye = p.get('eye', 'open')
        state = EYE_MAP.get(eye, eye)
        els = []
        for L in MAN['layers']:
            n = L['name']
            if n in ('boot_l', 'boot_r'):
                els.append(('piece', n, rect(n), boot_matrix(n, p, M, kx, ky), 'near' if n == 'boot_l' else 'far'))
            elif n in ('hand_0', 'hand_1'):
                i = int(n[-1])
                c = hand_center(i, p.get('wingF' if i == 0 else 'wingN', 4.0), p.get('spread', 0.0))
                c0 = hand_center(i, 4.0, 0.0)
                grp = 'near' if i == 0 or p.get('hand1_front') else 'far'
                els.append(('piece', n, rect(n), M @ T3(c[0] - c0[0], c[1] - c0[1]), grp))
            elif n.startswith('eye_'):
                i = int(n[-1])
                r = MAN['eyeStates'][state]['eye_%d' % i]['rect']
                rr = (r['x'], r['y'], r['w'], r['h'])
                E = Fe
                if eye == 'blink':
                    cx, cy = rr[0] + rr[2] / 2, rr[1] + rr[3] / 2
                    E = Fe @ T3(cx, cy) @ S3(1, 0.12) @ T3(-cx, -cy)
                els.append(('piece', ('eye', state, i), rr, M @ E, 'split'))
            elif n == 'beak_lower':
                dy = BEAK_OPEN * p.get('beak', 0.0)
                cav = cavity(round(dy))
                if cav is not None:
                    img, (bx, by) = cav
                    els.append(('image', img, (bx, by, img.shape[1], img.shape[0]), M @ Fb, 'split'))
                els.append(('piece', n, rect(n), M @ Fb @ T3(0, dy), 'split'))
            elif n == 'beak_upper':
                els.append(('piece', n, rect(n), M @ Fb, 'split'))
            elif n == 'bandana_tail':
                els.append(('tail', tail_dev(p, lean), None, M, 'split'))
            else:
                els.append(('piece', n, rect(n), M, 'split'))
        return els, M

    def render(self, V, p, size, part='all'):
        """Premultiplied RGBA (H, W, 4) of the duck. V: world -> layer continuous (3x3).
        part: 'all', or 'far' / 'near' for the seated split (see module doc)."""
        W, H = size
        layer = np.zeros((H, W, 4), np.float32)
        els, M = self.elements(p)
        VM = V @ M
        sig = math.sqrt(abs(np.linalg.det(VM[:2, :2])))        # layer px per duck px
        smax = float(np.linalg.svd(VM[:2, :2], compute_uv=False)[0])
        keep = None
        if part != 'all':
            Mi = np.linalg.inv(VM)
            xd = Mi[0, 0] * (np.arange(W, dtype=np.float32)[None, :] + 0.5) + \
                Mi[0, 1] * (np.arange(H, dtype=np.float32)[:, None] + 0.5) + Mi[0, 2]
            edge = (xd - (SPLIT_X - SPLIT_PAD)) if part == 'far' else ((SPLIT_X + SPLIT_PAD) - xd)
            keep = np.clip(edge * sig + 0.5, 0, 1).astype(np.float32)
        for kind, key, rr, Me, grp in els:
            if part != 'all' and grp in ('far', 'near') and grp != part:
                continue
            kp = keep if (part != 'all' and grp == 'split') else None
            A = V @ Me
            if kind == 'tail':
                sr = TS * smax                                     # layer px per tail-rig unit
                L = TAIL.length + 80
                org = (TAIL_TARGET[0] - L, TAIL_TARGET[1] - L)
                n = max(2, int(math.ceil(2 * L * sr)))
                sp = TR.chain_spine(key, TAIL.length, TAIL_AXIS, 0.0)
                img = TAIL.render(sp, TAIL_TARGET, org, (n, n), scale=sr)
                put(layer, img, UNHALF @ A @ S3(TS, TS) @ T3(*org) @ S3(1 / sr, 1 / sr) @ HALF, kp)
                continue
            x, y, w, h = rr
            s = float(np.linalg.svd(A[:2, :2], compute_uv=False)[0])
            sw, sh = max(1, round(w * s)), max(1, round(h * s))
            if kind == 'image':
                img = key if (sw, sh) == (key.shape[1], key.shape[0]) else np.clip(
                    cv2.resize(key, (sw, sh), interpolation=cv2.INTER_AREA if sw < key.shape[1] else cv2.INTER_CUBIC), 0, 1)
            else:
                img = self.small(key, sw, sh)
            put(layer, img, UNHALF @ A @ T3(x, y) @ S3(w / sw, h / sh) @ HALF, kp)
        return layer


# ---------------------------------------------------------------- self-check
def check():
    """Rest pose at 1:1 against the flat render, and the seated split's two halves against the whole."""
    ref = load('duck-final-1856x1280.png').astype(np.float32) / 255
    duck, V, p = Duck(), np.eye(3), dict(x=FOOT[0], y=FOOT[1], k=1.0)
    L = duck.render(V, p, (CW, CH))
    a, ra = L[..., 3], ref[..., 3]
    iou = ((a > .5) & (ra > .5)).sum() / ((a > .5) | (ra > .5)).sum()
    m = (a > .99) & (ra > .99)
    rgb = L[..., :3] / np.maximum(a[..., None], 1e-6)
    print(f'rest vs duck-final-1856x1280.png: alpha IoU {iou:.4f}, mean colour |d| {np.abs(rgb[m] - ref[..., :3][m]).mean() * 255:.2f}/255')
    far, near = (duck.render(V, p, (CW, CH), part=s) for s in ('far', 'near'))
    d = np.abs(far[..., 3] * (1 - near[..., 3]) + near[..., 3] - a)
    xs = np.nonzero((d > 0.05).any(0))[0]
    print(f'far + near vs whole: {int((d > 0.05).sum())} px differ by > 0.05 alpha'
          + (f', all in x {xs.min()}-{xs.max()} (split {SPLIT_X:.0f} +- {SPLIT_PAD:.0f})' if len(xs) else ''))


if __name__ == '__main__':
    check()
