"""Neck + mane swing rig for the horse-upper pack (preview only).

render(neck_deg, head_deg, block_degs, hair_deg) returns one premultiplied
RGBA frame in body-local space (the body and saddle stay still; front= swaps
in another body + saddle layer, e.g. the haunch warp of horse-legs/haunch.py):

* Layer order: neck -> head -> body -> saddle. The neck sits BEHIND the body
  and saddle and is extended downwards (EXT) and to the left under them, so no
  gap opens when it turns. The extension is only allowed to show under the
  body / saddle and in the neck-body gap in front of the saddle. Columns on the
  slanted chest edge (neck px u > FRONT_U) are not extended: that would hang a
  black curtain under the front outline.
* The neck bends instead of turning rigidly: the angle fades in along the
  neck axis (NECK_PIVOT -> HEAD_PIVOT) with smoothstep(BEND_S0, BEND_S1), so
  the withers, saddle and chest junctions stay put. The head follows the full
  angle, plus its own head_deg about HEAD_PIVOT.
* Mane: six code-generated blocks (ink outline + dark fill, mane.json) swing
  about pivots on the inner edge of the mane-root band. A stepped dark base
  (the drawn mane outline eroded 18px) lies under them and only shows where
  blocks swing apart; blocks and base cast soft shadows; everything is
  clipped to the visible neck and the root band is laid back on top.
* Forelock: the head manifest's hair layer swings about its root and stays
  clipped behind the front ear (clipPolygon).

Pieces: ../pieces/{body,neck}.png, ../placements.json,
assets/horse-saddle/saddle.png, assets/horse-head/ (manifest + pieces).
Canvas constants (EXT, FRONT_U, saddle top y=975, gap x>=1294, bend range)
are tuned for the current placements.
"""

import json
import math
import os

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.dirname(HERE)                 # assets/horse-upper
ASSETS = os.path.dirname(PACK)               # assets/


def read_json(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)


PL = {p['name']: p for p in read_json(os.path.join(PACK, 'placements.json'))['placements']}
def xy(n): return (PL[n]['x'], PL[n]['y'])
BODY_XY, BODY_S = xy('body'), PL['body']['scale']
SADDLE_XY, SADDLE_S = xy('saddle'), PL['saddle']['scale']
NECK_XY, NECK_S = xy('neck'), PL['neck']['scale']
HEAD_XY, HEAD_S = xy('head'), PL['head']['scale']

RS = 0.75                                    # render px per 2048-canvas px
FX0, FY0, FX1, FY1 = 40, -300, 2800, 1960    # render frame on the 2048 canvas
FW, FH = round((FX1 - FX0) * RS), round((FY1 - FY0) * RS)
NECK_PIVOT = (1620, 1225)                    # neck base centroid (2048 canvas)
HEAD_PIVOT = (1947, 400)                     # poll / head-neck joint
F = NECK_S * RS
PADL, PADT, PADR, PADB = 70, 12, 12, 300


def load(p): return np.array(Image.open(p).convert('RGBA')).astype(np.float32) / 255.0
def premul(a): b = a.copy(); b[..., :3] *= b[..., 3:4]; return b
def over(dst, src): dst *= (1 - src[..., 3:4]); dst += src; return dst
def kern(n): n = max(1, int(round(n))); return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (n, n))


def nearest_idx(mask):
    d, lab = cv2.distanceTransformWithLabels((~mask).astype(np.uint8), cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    ys, xs = np.where(mask)
    ly = np.zeros(lab.max() + 1, np.int32); lx = np.zeros(lab.max() + 1, np.int32)
    zl = lab[mask]; ly[zl] = ys; lx[zl] = xs
    return ly[lab], lx[lab], d


# ================================================================ neck (native px)
nk = load(os.path.join(PACK, 'pieces', 'neck.png')); nh, nw = nk.shape[:2]
A = nk[..., 3]; R = nk[..., 0] * 255
VV, UU = np.mgrid[0:nh, 0:nw]
# mane-root band layer: the dark band pixels with their anti-aliased rim against the coat
coat_px = (A > 0.5) & (R >= 140)
bandish = (A > 0.5) & ~coat_px
cy, cx, dcoat = nearest_idx(coat_px)
deep = bandish & (dcoat > 2.5)
dy_, dx_, _ = nearest_idx(deep)
rim = bandish & (dcoat <= 2.5)
p = nk[..., :3]; b = nk[dy_, dx_, :3]; c = nk[cy, cx, :3]
bc = b - c
cov_rim = np.clip(((p - c) * bc).sum(-1) / np.maximum((bc * bc).sum(-1), 1e-4), 0, 1)
cov = np.where(deep, 1.0, np.where(rim, cov_rim, 0.0)).astype(np.float32)
band_rgb = np.where(deep[..., None], p, b)
band_layer = np.dstack([band_rgb, cov * A]).astype(np.float32)
band_mane = (R < 95) & (A > 0.5) & ((UU < 300) | (VV < 50))   # crest band only (not the throat outline)

MANE = read_json(os.path.join(HERE, 'mane.json'))
BLOCKS = [(m['top'], m['right'], m['bottom']) for m in MANE['blocks']]
PIVOTS = [tuple(m['pivot']) for m in MANE['blocks']]
TOP_EXT = [m.get('topExt', 0) for m in MANE['blocks']]
BW, INS = MANE['blockWidth'], MANE['innerInset']
S = np.zeros((nh, nw), np.uint8)             # drawn mane outline
cv2.drawContours(S, [np.array(MANE['underlay']['contour'], np.int32).reshape(-1, 1, 2)], -1, 1, -1)
S = S.astype(bool)

# ================================================================ NC: neck render space (F px per neck px)
NW_, NH_ = round(nw * F), round(nh * F)
NCW, NCH = NW_ + PADL + PADR, NH_ + PADT + PADB
SX, SY = NW_ / nw, NH_ / nh
def to_nc(u, v): return (PADL + u * SX, PADT + v * SY)


def up_nc(a):
    out = np.zeros((NCH, NCW) + a.shape[2:], np.float32)
    out[PADT:PADT + NH_, PADL:PADL + NW_] = np.clip(cv2.resize(a, (NW_, NH_), interpolation=cv2.INTER_LANCZOS4), 0, 1)
    return out


neck_nc = up_nc(premul(nk)); band_nc = up_nc(premul(band_layer))
alpha_nc = neck_nc[..., 3].copy()
# ---- extensions (hidden under body / saddle; fill gaps when the neck moves)
solid = alpha_nc > 0.98
neck_full = neck_nc.copy(); ext_mask = np.zeros((NCH, NCW), np.float32)
EXT = 210
FRONT_U = 303                                # neck px: columns right of this end on the slanted chest edge, not on the base
for x in range(NCW):
    if (x - PADL) / SX > FRONT_U: continue   # extending those would hang a black curtain under the front outline
    ys = np.where(solid[:, x])[0]
    if len(ys) < 20: continue
    yb = ys.max(); src = np.median(neck_nc[yb - 14:yb - 4, x, :3], axis=0)
    y0, y1 = yb - 3, min(NCH, yb + EXT)
    neck_full[y0:y1, x, :3] = src; neck_full[y0:y1, x, 3] = 1; ext_mask[y0:y1, x] = 1
y_sad = int(round(to_nc(0, (975 - NECK_XY[1]) / NECK_S)[1]))
solid2 = neck_full[..., 3] > 0.98
for y in range(y_sad, NCH):
    xs = np.where(solid2[y])[0]
    if len(xs) < 10: continue
    xl = xs.min(); col = np.median(neck_full[y, xl + 8:xl + 18, :3], axis=0)
    if col.sum() < 1.2: continue             # band rows: no left extension (stays behind the saddle)
    x0 = max(0, xl - 64)
    neck_full[y, x0:xl + 4, :3] = col; neck_full[y, x0:xl + 4, 3] = 1; ext_mask[y, x0:xl + 4] = 1
rows = np.mgrid[0:NCH, 0:NCW][0]
hole = (neck_full[..., 3] < 0.98) & (cv2.morphologyEx((neck_full[..., 3] > 0.98).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8)) > 0) & (rows >= y_sad)
if hole.any():
    filled = cv2.inpaint((neck_full[..., :3] * 255).astype(np.uint8), hole.astype(np.uint8), 5, cv2.INPAINT_TELEA).astype(np.float32) / 255
    neck_full[hole, :3] = filled[hole]; neck_full[hole, 3] = 1; ext_mask[hole] = 1
blur = cv2.GaussianBlur(neck_full[..., :3], (0, 0), 1.2); m = cv2.GaussianBlur(ext_mask, (0, 0), 1.5)[..., None]
neck_full[..., :3] = neck_full[..., :3] * (1 - m) + blur * m
# ---- mane window (all block painting happens inside it)
WX0, WY0 = [int(v) for v in to_nc(-8, 80)]; WX1, WY1 = [int(v) for v in to_nc(250, 455)]
WX0 = max(0, WX0)
Vf = (np.clip(alpha_nc, 0, 1) * (1 - ext_mask))[WY0:WY1, WX0:WX1]  # blocks: visible neck only
Vs = np.clip(neck_full[..., 3], 0, 1)[WY0:WY1, WX0:WX1]            # shadows may also fall on the hidden extension
def rect(x0, y0, x1, y1): return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
BL_OUT = [rect(r - BW, t - e, r, b_) for (t, r, b_), e in zip(BLOCKS, TOP_EXT)]
BL_IN = [rect(r - BW, t + INS['top'] - e, r - INS['right'], b_ - INS['bottom']) for (t, r, b_), e in zip(BLOCKS, TOP_EXT)]


def rot(pts, p, deg):
    a = math.radians(deg); c_, s_ = math.cos(a), math.sin(a)
    return [(p[0] + (x - p[0]) * c_ - (y - p[1]) * s_, p[1] + (x - p[0]) * s_ + (y - p[1]) * c_) for x, y in pts]


def polymask(pts):
    mm = np.zeros((WY1 - WY0, WX1 - WX0), np.uint8)
    q = (np.array([to_nc(x, y) for x, y in pts]) - [WX0, WY0]) * 16
    cv2.fillPoly(mm, [np.round(q).astype(np.int32)], 255, lineType=cv2.LINE_AA, shift=4)
    return mm.astype(np.float32) / 255


# ---- underlay: inset stepped dark base, hidden under the blocks at rest
rest_cover = np.zeros((nh, nw), bool)
for (t, r, b_), e in zip(BLOCKS, TOP_EXT): rest_cover[max(0, t - e):b_ + 1, :r + 1] = True
rest_cover &= A > 0.5
U = (cv2.dilate(band_mane.astype(np.uint8), kern(17)) > 0) & ~band_mane & (A > 0.5) & rest_cover & (VV >= 90) & (VV <= 405)
Sx = cv2.morphologyEx((S | U).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)) > 0
R_INSET = 18
er = cv2.erode(Sx.astype(np.uint8), np.ones((R_INSET + 1, R_INSET + 1), np.uint8), anchor=(0, 0)) > 0
base_native = ((er | U) & (A > 0.5)).astype(np.float32)
base_w = cv2.GaussianBlur(up_nc(base_native), (0, 0), 0.7)[WY0:WY1, WX0:WX1]
base_in_w = cv2.GaussianBlur(up_nc((cv2.erode(base_native, np.ones((7, 7), np.uint8)) > 0.5).astype(np.float32)), (0, 0), 0.7)[WY0:WY1, WX0:WX1]
FILL = np.array([46, 38, 32.], np.float32) / 255; BASEF = np.array([38, 31, 27.], np.float32) / 255; INK = np.array([14, 9, 8.], np.float32) / 255
SH_MUL = np.array([.80, .72, .56], np.float32); RIM_MUL = np.array([.55, .5, .42], np.float32)
K5, K3 = kern(5 * F), kern(3 * F); SHY, SHX = round(4 * F), round(1 * F)


def shadow(C, mm):
    sm = np.roll(np.roll(cv2.dilate(mm, K5), SHY, 0), SHX, 1)
    sm = cv2.GaussianBlur(sm, (0, 0), 1.3 * F)[..., None] * Vs[..., None]
    C[..., :3] *= 1 - sm * (1 - SH_MUL)
    rm = cv2.GaussianBlur(cv2.dilate(mm, K3), (0, 0), 0.8 * F)[..., None] * Vs[..., None]
    C[..., :3] *= 1 - rm * (1 - RIM_MUL)


def paint(C, mm, col):
    mm = (mm * Vf)[..., None]; C[..., :3] = C[..., :3] * (1 - mm) + col * mm * C[..., 3:4]


band_w = band_nc[WY0:WY1, WX0:WX1]


def render_neck(angles, with_base=True):
    C = neck_full.copy(); W = C[WY0:WY1, WX0:WX1]
    if with_base:
        shadow(W, base_w); paint(W, base_w, INK); paint(W, base_in_w, BASEF)
    for o, i, p_, a in zip(BL_OUT, BL_IN, PIVOTS, angles):
        mo = polymask(rot(o, p_, a)); mi = polymask(rot(i, p_, a))
        shadow(W, mo); paint(W, mo, INK); paint(W, mi, FILL)
    over(W, band_w)
    return C


# ================================================================ frame space
def c2f(x, y): return ((x - FX0) * RS, (y - FY0) * RS)
def T3(tx, ty): return np.array([[1, 0, tx], [0, 1, ty], [0, 0, 1.]])


def R3(deg, cx, cy):
    a = math.radians(deg); c_, s_ = math.cos(a), math.sin(a)
    return np.array([[c_, -s_, cx - c_ * cx + s_ * cy], [s_, c_, cy - s_ * cx - c_ * cy], [0, 0, 1]])


def warp(img, M, size=(FW, FH)):
    return cv2.warpAffine(img, M[:2], size, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))


def prescale(a, sx_total):
    h, w = a.shape[:2]; W, H = max(1, round(w * sx_total)), max(1, round(h * sx_total))
    return np.clip(cv2.resize(premul(a), (W, H), interpolation=cv2.INTER_AREA if sx_total < 1 else cv2.INTER_LANCZOS4), 0, 1)


body_f = warp(prescale(load(os.path.join(PACK, 'pieces', 'body.png')), BODY_S * RS), T3(*c2f(*BODY_XY)))
saddle_f = warp(prescale(load(os.path.join(ASSETS, 'horse-saddle', 'saddle.png')), SADDLE_S * RS), T3(*c2f(*SADDLE_XY)))
front_f = over(body_f.copy(), saddle_f)
# where the neck extension may show: under body/saddle, or in the neck-body gap right of the saddle front
bs = ((body_f[..., 3] > 0.01) | (saddle_f[..., 3] > 0.01)).astype(np.uint8)
bs = cv2.dilate(bs, kern(5)) > 0
bm = body_f[..., 3] > 0.01
has = bm.any(0); top = np.where(has, bm.argmax(0), 0)
YYf, XXf = np.mgrid[0:FH, 0:FW]
gapzone = (XXf >= c2f(1294, 0)[0]) & (YYf < top[None, :]) & has[None, :]
ext_allowed = (bs | gapzone).astype(np.float32)
M_nc = T3(c2f(*NECK_XY)[0] - PADL, c2f(*NECK_XY)[1] - PADT)
# ---- head (head-local px -> HL px, scale HS)
HS = HEAD_S * RS; HPAD = 60
HEAD_DIR = os.path.join(ASSETS, 'horse-head')
man = read_json(os.path.join(HEAD_DIR, 'manifest.json'))
HW, HH = round(man['canvas']['w'] * HS) + 2 * HPAD, round(man['canvas']['h'] * HS) + 2 * HPAD
def h2l(x, y): return (HPAD + x * HS, HPAD + y * HS)


parts = {}
for L in man['layers']:
    r = L['rect']; a = load(os.path.join(HEAD_DIR, L['file']))
    Wp, Hp = round(r['w'] * HS), round(r['h'] * HS)
    img = np.clip(cv2.resize(premul(a), (Wp, Hp), interpolation=cv2.INTER_AREA if Wp < a.shape[1] else cv2.INTER_LANCZOS4), 0, 1)
    parts[L['name']] = (img, h2l(r['x'], r['y']))
head_base = np.zeros((HH, HW, 4), np.float32)
for n in ('ear_back', 'ear_front', 'head'):
    img, (x, y) = parts[n]; over(head_base, warp(img, T3(x, y), (HW, HH)))
eye_l = warp(parts['eye'][0], T3(*parts['eye'][1]), (HW, HH))
HAIR = next(L for L in man['layers'] if L['name'] == 'hair')
hr = HAIR['rect']
HAIR_ROOT = (14, 20)                         # hair-local px: forelock root, next to the front ear
HAIR_PIVOT = h2l(hr['x'] + HAIR_ROOT[0], hr['y'] + HAIR_ROOT[1])
# clipPolygon notch corner = front ear's right / bottom edge (hair-local); the clip stays fixed while the hair swings
notch = [q for q in HAIR.get('clipPolygon', []) if 0 < q[0] < hr['w'] and 0 < q[1] < hr['h']] or [(10, 39)]
EAR_CLIP = [int(round(v)) for v in h2l(hr['x'] + notch[0][0], hr['y'] + notch[0][1])]


def render_head(hair_deg):
    C = head_base.copy()
    img, (x, y) = parts['hair']
    w = warp(img, R3(hair_deg, *HAIR_PIVOT) @ T3(x, y), (HW, HH))
    w[:EAR_CLIP[1], :EAR_CLIP[0]] = 0          # tucks behind the front ear
    over(C, w); over(C, eye_l)
    return C


M_hl = T3(c2f(*HEAD_XY)[0] - HPAD, c2f(*HEAD_XY)[1] - HPAD)
# ---- neck bend: the rotation fades out toward the neck base, so the withers/saddle and chest junctions stay put
BX0, BY0 = [max(0, int(v)) for v in c2f(1000, -150)]; BX1, BY1 = [int(v) for v in c2f(2250, 1700)]
BX1, BY1 = min(FW, BX1), min(FH, BY1)
_gy, _gx = np.mgrid[BY0:BY1, BX0:BX1].astype(np.float32)
QX = _gx / RS + FX0 - NECK_PIVOT[0]; QY = _gy / RS + FY0 - NECK_PIVOT[1]
_ax, _ay = HEAD_PIVOT[0] - NECK_PIVOT[0], HEAD_PIVOT[1] - NECK_PIVOT[1]
_s = (QX * _ax + QY * _ay) / (_ax * _ax + _ay * _ay)          # 0 at the neck base, 1 at the poll
BEND_S0, BEND_S1 = 0.12, 0.60
_t = np.clip((_s - BEND_S0) / (BEND_S1 - BEND_S0), 0, 1); W_BEND = (_t * _t * (3 - 2 * _t)).astype(np.float32)
NCOFF = (c2f(*NECK_XY)[0] - PADL, c2f(*NECK_XY)[1] - PADT)


def bend_warp(img, deg):
    ph = np.radians(deg) * W_BEND; c_, s_ = np.cos(ph), np.sin(ph)
    sx = QX * c_ + QY * s_; sy = -QX * s_ + QY * c_            # inverse rotation of the output point
    mx = ((sx + NECK_PIVOT[0] - FX0) * RS - NCOFF[0]).astype(np.float32)
    my = ((sy + NECK_PIVOT[1] - FY0) * RS - NCOFF[1]).astype(np.float32)
    out = np.zeros((FH, FW) + img.shape[2:], np.float32)
    out[BY0:BY1, BX0:BX1] = cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return out


def render(neck_deg, head_deg, block_degs, hair_deg, with_base=True, bend=True, front=None):
    """Premultiplied RGBA frame (FH x FW, body-local, body static). Degrees, positive = clockwise on screen.
    front: body + saddle layer laid on top (default front_f)."""
    Rn = R3(neck_deg, *c2f(*NECK_PIVOT))
    Mn = Rn @ M_nc
    if bend:
        out = bend_warp(render_neck(block_degs, with_base), neck_deg)
        em = bend_warp(ext_mask, neck_deg)
    else:                                    # rigid turn, for comparison
        out = warp(render_neck(block_degs, with_base), Mn)
        em = cv2.warpAffine(ext_mask, Mn[:2], (FW, FH), flags=cv2.INTER_LINEAR)
    frac = np.clip(em / np.maximum(out[..., 3], 1e-4), 0, 1)        # share of each pixel that comes from the extension
    out *= (1 - frac * (1 - ext_allowed))[..., None]
    over(out, warp(render_head(hair_deg), Rn @ R3(head_deg, *c2f(*HEAD_PIVOT)) @ M_hl))
    over(out, front_f if front is None else front)
    return out


def on_bg(out, bg=(1, 1, 1)):
    return np.clip(np.array(bg, np.float32) * (1 - out[..., 3:4]) + out[..., :3], 0, 1)
