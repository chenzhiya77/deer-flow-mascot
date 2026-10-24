"""Five keyframes of the opening with the final duck and the new horse: perched on the book tower, looking
down at the horse, hanging in the air before the drop, chasing the horse, riding off with a shout.

Each keyframe is one instant of the opening's timeline (story time T, s): the duck's pose is the opening's
duckPose at T (table KEYS below), the horse is the leg / tail / neck rig of ../../horse-legs at preview time
T - 1.9 (that preview runs the opening's mount / gait timeline 1.9 s earlier), placed where the opening puts
its horse. The world is the 2048 horse canvas: opening (u, v) -> (5.70 u, 2630 + 5.70 (v - 848)), 5.70 px
per opening unit being the saddle height (1579 px) over the opening's seat height (277 units); the duck is
drawn at 0.877 (its 0.39 riding scale / the horse's 0.4445). The camera follows the opening's camX / camY
(1 opening unit = 1 frame px); the book tower is a flat placeholder in the opening's sizes and colours, on a
neutral stage.

Layering: on the tower the duck is behind the horse (the tower stands behind the horse's path); after the
drop it is in front; seated it is split at its middle (right half behind the horse, left half in front).

Usage:
  python keyframes.py                 # -> <repo>/out/final-duck-keyframes/kf1..5.png, kf1..5-close.png, sheets
  python keyframes.py --only 2 5      # just these keyframes (no sheets)
"""
import argparse
import math
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ASSETS, 'horse-legs'))
import duckrig as D  # noqa: E402
import gait_preview as GP  # noqa: E402  (horse: legs, tail, bust; also puts horse-upper/motion on sys.path)

PV, GT, G, HN, TR, TP, R = GP.PV, GP.GT, GP.G, GP.HN, GP.TR, GP.TP, GP.R
OUT = os.path.join(PV.OUT_DIR, 'final-duck-keyframes')
W, H = 1920, 1080

# ---------------------------------------------------------------- world
PXU = 1579 / 277          # px per opening unit
KD = 0.39 / 0.4445        # duck px -> horse canvas px
GROUND_V = 848            # opening GROUND_Y: the horse's hooves
LANE_V = 866              # opening DUCK.lane: the duck runs a little in front of the horse
SEAT_C = (854.0, 1051.0)  # saddle dip on the horse canvas <-> opening seat (horseX + 2, GROUND_Y - 277)
SEAT_CLEAR = 2.0          # box bottom this many px above the saddle outline
T_SHIFT = 1.9             # story time - horse preview time


def wx(u):
    return PXU * u


def wy(v):
    return G.GROUND + PXU * (v - GROUND_V)


# horse x on the opening timeline (timeline.ts): saddle under the perch at the drop beat, walk 349 u/s,
# speeding up to 1400 u/s over the gait change 5.0-5.75 s; same Euler steps as the opening
_DT = 1 / 600
_XH = [700 - 349 * 2.35]
for _i in range(int(11.2 / _DT)):
    _T = _i * _DT
    _XH.append(_XH[-1] + PV.lerp(349, 1400, PV.smooth(5.0, 5.75, _T)) * _DT)


def horse_x(T):
    f = T / _DT
    i = int(f)
    return _XH[i] + (_XH[i + 1] - _XH[i]) * (f - i)


# ---------------------------------------------------------------- horse before the preview's t = 0
# keyframe 1 is 0.7 s before the horse preview starts, the opening (opening_preview.py) 1.9 s; the walk is steady
# there, so phases extend linearly
PRE = 2.0
_samp = PV.samp


def _samp_ext(a, T):
    return _samp(a, T) if T >= 0 else a[0] + (a[1] - a[0]) / PV.DT * T


PV.samp = _samp_ext       # params() / tail_dev() read their phase tables through PV.samp
_t = np.arange(-PRE, PV.DUR + 1, PV.DT)
_v = np.array([PV.speed(t) for t in _t]) * GT.UNIT
GAIT = GT.Gait([PV.samp(PV.PHI, t) for t in _t], [PV.gblend(t) for t in _t],
               np.concatenate([[0.0], np.cumsum((_v[1:] + _v[:-1]) / 2 * PV.DT)]), PV.DT)


def body(p, dip=0.0):
    """Body matrix (canvas) of the horse in pose p = PV.params(tp); dip = extra bob, opening units (+ down)."""
    return R.T3(0, (p['bob'] / GP.NECK_BOB + dip) * GT.BOB_UNIT) @ R.R3(p['pitch'], *PV.CB)


def horse_state(tp, dip=0.0):
    """gait_preview.frame_state at preview time tp (may be negative), body lowered by dip (see body)."""
    p = PV.params(tp)
    B = body(p, dip)
    legs = GT.poses(GAIT, tp + PRE, p['g'], B)
    th = HN.angle(legs, p['pitch'])
    mp = HN.maps(th)
    return dict(p=p, B=B, legs=legs, haunch=th, scroll=0.0,
                spine=TR.chain_spine(TP.tail_dev(tp), TP.L, G.TAIL_AXIS, G.SPINE_N),
                fr=R.render(p['neck'], p['head'], p['blocks'], p['hair'], front=HN.front(th, mp)),
                seam=HN.seam(th, mp))


# ---------------------------------------------------------------- keyframes
# duck pose = the opening's duckPose(T) (rounded); eye 'xiakan' at 1.9: the opening's 'determined' while
# looking down (ly .95) -> the final duck's looking-down eyes. KF5 is seated: dx / dy are the riding spring's
# offsets from the seat (opening units), its lean the opening's minus the old horse's body pitch (3.52 deg;
# this horse's own pitch is added back). cam = the opening's camX / camY. close = close-up centre (u, v) and
# frame px per opening unit.
KEYS = [
    dict(n=1, name='站书堆', T=1.20, cam=(0, 0), close=((700, 300), 4.4), place='tower',
         duck=dict(x=700, y=395, sx=1.006, sy=0.992, head=-2.6, wingN=4, wingF=6, legs='stand', eye='open',
                   lx=0.871, ly=-0.1)),
    dict(n=2, name='低头看马', T=1.90, cam=(0, 0), close=((705, 378), 2.75), place='tower',
         duck=dict(x=700, y=395, sx=0.995, sy=1.006, head=13.19, wingN=4, wingF=6, legs='stand', eye='xiakan',
                   lx=-0.35, ly=0.95)),
    dict(n=3, name='空中一顿，开始下落', T=2.82, cam=(0, 10.75), close=((745, 445), 2.9), place='air',
         duck=dict(x=712, y=503.35, sx=0.914, sy=1.196, head=-8, wingN=120.21, wingF=108.5, spread=1, legs='dangle',
                   eye='shock', ly=-0.9, beak=0.85, vy=1372.8)),
    dict(n=4, name='追马', T=3.90, cam=(183.35, 0.35), close=((1060, 635), 2.15), place='lane',
         duck=dict(x=883.05, y=860.81, rot=16.70, sx=1.015, sy=0.98, head=-4.61, wingN=41.03, wingF=2.71, legs='run',
                   legPhase=4.334, eye='determined', lx=1, ly=-0.1, vx=455.1)),
    dict(n=5, name='骑马喊“出发！”', T=5.45, cam=(1215.18, 0), close=((1935, 600), 2.25), place='seat',
         duck=dict(dx=-0.88, dy=-0.38, rot=-4.48 - 3.52, sx=0.992, sy=1.013, head=-4.07, wingN=150.89, wingF=24.18,
                   spread=0.85, legs='sit', eye='determined', lx=1, ly=0, beak=0.8, vx=1030.05, sit=1)),
]


def scene(key):
    """Horse state, horse canvas -> world offset, duck pose (world) and duck layering for one keyframe."""
    T = key['T']
    st = horse_state(T - T_SHIFT)
    dxh = wx(horse_x(T) + 2) - SEAT_C[0]
    d = dict(key['duck'], k=KD, T=T)
    if key['place'] == 'seat':
        sx, sy = D.apply(st['B'], *SEAT_C)
        d['x'], d['y'] = sx + dxh + PXU * d.pop('dx'), sy + PXU * d.pop('dy') - SEAT_CLEAR
        d['rot'] += st['p']['pitch']
    else:
        d['x'], d['y'] = wx(d['x']), wy(d['y'])
    d['ground'] = {'tower': wy(395), 'lane': wy(LANE_V)}.get(key['place'])
    return st, dxh, d


# ---------------------------------------------------------------- stage
BG = np.array([247, 245, 240], np.float32) / 255
FILL = np.array([236, 231, 222], np.float32) / 255
EDGE = np.array([206, 197, 185], np.float32) / 255
MARK = np.array([214, 206, 194], np.float32) / 255
SHADOW = np.array([120, 104, 88], np.float32) / 255
BACK_V = 800              # back edge of the ground band
TOWER_X, TOWER_BASE, PAGE_W, PAGE_COL = 700, 811, 15, (235, 217, 191)
BOOKS = [  # bottom -> top: height, width, x offset, tilt (deg), cover, band (opening book tower sizes / colours)
    (70, 198, -4, 0.0, (122, 46, 58), (226, 176, 98)), (58, 178, 9, -1.3, (31, 94, 99), (230, 190, 116)),
    (66, 188, -7, 1.0, (168, 114, 44), (243, 208, 140)), (52, 166, 11, -0.7, (39, 59, 106), (221, 180, 108)),
    (62, 180, -9, 1.4, (91, 46, 94), (232, 184, 112)), (56, 156, 6, -1.0, (46, 90, 62), (230, 192, 122)),
    (52, 142, 1, 0.4, (142, 63, 42), (240, 194, 124))]


def hashf(n, salt):
    return ((int(n) * 2654435761 + salt * 40503) % 4294967296) / 4294967296


def to_layer(V, X, Y):
    return V[0, 0] * X + V[0, 2] - 0.5, V[1, 1] * Y + V[1, 2] - 0.5   # world -> layer px (index space)


def ground(img, V):
    s = V[0, 0] * PXU                                  # frame px per opening unit
    y0 = to_layer(V, 0, wy(BACK_V))[1]
    rows = np.arange(H, dtype=np.float32)
    a = np.clip(rows - y0 + 0.5, 0, 1)[:, None, None]
    img[:] = img * (1 - a) + FILL * a
    ink = np.zeros((H, W), np.uint8)
    S16 = 16
    cv2.line(ink, (0, int(round(y0 * S16))), (W * S16, int(round(y0 * S16))), 255, max(1, round(1.6 * s)), cv2.LINE_AA, 4)
    marks = np.zeros((H, W), np.uint8)
    u0, u1 = (0 - V[0, 2]) / V[0, 0] / PXU, (W - V[0, 2]) / V[0, 0] / PXU
    for n in range(int(u0 // 36) - 2, int(u1 // 36) + 2):    # dashes fixed on the ground, every ~36 units
        u = n * 36 + 30 * hashf(n, 1)
        v = BACK_V + 14 + 200 * hashf(n, 2) ** 1.4
        ln = (6 + 16 * hashf(n, 3)) * (0.7 + 0.5 * (v - BACK_V) / 200)
        x0, yy = to_layer(V, wx(u), wy(v))
        x1 = x0 + V[0, 0] * PXU * ln
        cv2.line(marks, (int(round(x0 * S16)), int(round(yy * S16))), (int(round(x1 * S16)), int(round(yy * S16))), 255,
                 max(1, round(1.4 * s)), cv2.LINE_AA, 4)
    for m, col in ((marks, MARK), (ink, EDGE)):
        al = (m.astype(np.float32) / 255)[..., None]
        img[:] = img * (1 - al) + col * al


def shadows(img, V, ells, clip=None):
    """Soft contact shadows: world ellipses (x, y, rx, ry, strength 0-255), blurred; clip = alpha to keep them on."""
    k = V[0, 0]
    sh = np.zeros((H, W), np.uint8)
    S16 = 16
    for X, Y, ax, ay, val in ells:
        x, y = to_layer(V, X, Y)
        cv2.ellipse(sh, (int(round(x * S16)), int(round(y * S16))), (max(1, int(round(ax * k * S16))),
                    max(1, int(round(ay * k * S16)))), 0, 0, 360, int(val), -1, cv2.LINE_AA, 4)
    m = cv2.GaussianBlur(sh, (0, 0), max(1.0, 7 * k)).astype(np.float32)[..., None] / 255
    if clip is not None:
        m = m * clip
    img[:] = img * (1 - 0.22 * m) + SHADOW * 0.22 * m


def horse_shadows(st, dxh):
    """The horse's body and hooves, as in gait_preview.ground."""
    out = [(1060 + dxh, G.GROUND + 6, 1000, 44, 120)]
    for kk, q in st['legs'].items():
        Dm = GT.DIMS[kk]
        toe, heel = q['fet'] + GT.rot(Dm['toe'], q['a_hoof']), q['fet'] + GT.rot(Dm['heel'], q['a_hoof'])
        a = GT.clamp(1 - (G.GROUND - max(toe[1], heel[1])) / 260, 0, 1)
        if a > 0:
            out.append(((toe[0] + heel[0]) / 2 + dxh, G.GROUND + 4, 110 * (0.75 + 0.25 * a), 18, 255 * a))
    return out


def duck_shadow(d, key):
    """The duck's, on the tower top or the lane (the opening's: smaller and fainter with height)."""
    if key['place'] not in ('tower', 'lane', 'air'):
        return []
    gy = wy(395) if key['place'] == 'tower' else wy(LANE_V)
    a = GT.clamp(1 - max(0.0, gy - d['y']) / (180 * PXU), 0, 1)
    if a <= 0:
        return []
    dy = 0 if key['place'] == 'tower' else 3 * PXU / 5.7
    return [(d['x'], gy + dy, 330 * (0.6 + 0.4 * a), 30, 230 * a)]


def tower(V):
    """Premultiplied layer of the placeholder book tower."""
    s = V[0, 0] * PXU
    SS = 3                                                 # supersampling
    x0, y0 = to_layer(V, wx(TOWER_X - 130), wy(395 - 12))
    x1, y1 = to_layer(V, wx(TOWER_X + 130), wy(TOWER_BASE + 6))
    bx0, by0, bx1, by1 = max(0, int(x0)), max(0, int(y0)), min(W, int(x1) + 1), min(H, int(y1) + 1)
    out = np.zeros((H, W, 4), np.float32)
    if bx1 <= bx0 or by1 <= by0:
        return out
    im = Image.new('RGBA', ((bx1 - bx0) * SS, (by1 - by0) * SS), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)

    def P(u, v):
        x, y = to_layer(V, wx(u), wy(v))
        return ((x - bx0 + 0.5) * SS, (y - by0 + 0.5) * SS)

    def quad(cx, cy, w, h, a, x0_, x1_, y0_, y1_):         # rect in book-local fractions, tilted a deg
        c, sn = math.cos(math.radians(a)), math.sin(math.radians(a))
        pts = []
        for fx, fy in ((x0_, y0_), (x1_, y0_), (x1_, y1_), (x0_, y1_)):
            lx, ly = (fx - 0.5) * w, (fy - 0.5) * h
            pts.append(P(cx + lx * c - ly * sn, cy + lx * sn + ly * c))
        return pts

    lw = max(1, round(2.2 * s * SS))
    v = TOWER_BASE
    for h, w, dx, a, cover, band in BOOKS:
        cx, cy = TOWER_X + dx, v - h / 2
        dark = tuple(int(c * 0.55) for c in cover)
        dr.polygon(quad(cx, cy, w, h, a, 0, 1, 0, 1), fill=cover + (255,), outline=(44, 32, 26, 255), width=lw)
        pf = PAGE_W / w
        dr.polygon(quad(cx, cy, w, h, a, 1 - pf - 0.01, 1 - 0.012, 0.12, 0.88), fill=PAGE_COL + (255,))
        for f in (0.32, 0.5, 0.68):
            dr.line(quad(cx, cy, w, h, a, 1 - pf, 1 - 0.02, f, f)[:2], fill=(205, 186, 160, 255), width=max(1, lw // 3))
        dr.polygon(quad(cx, cy, w, h, a, 0.10, 0.64, 0.30, 0.70), fill=band + (255,))
        dr.polygon(quad(cx, cy, w, h, a, 0.14, 0.60, 0.42, 0.58), fill=dark + (255,))
        v -= h
    small = cv2.resize(np.asarray(im, np.float32) / 255, (bx1 - bx0, by1 - by0), interpolation=cv2.INTER_AREA)
    out[by0:by1, bx0:bx1] = np.concatenate([small[..., :3] * small[..., 3:4], small[..., 3:4]], 2)
    return out


# ---------------------------------------------------------------- frame
_views = {}
DUCK = D.Duck()


def horse_view(V):
    k = round(V[0, 0], 6)
    if k not in _views:
        _views[k] = GP.View(k, (0, 0), (0, 0), (W, H))     # pieces prescaled to k; M set per frame
    return _views[k]


def over(img, L):
    img[:] = L[..., :3] + img * (1 - L[..., 3:4])


def frame(key, V, st=None):
    st_, dxh, d = scene(key) if st is None else st
    img = np.empty((H, W, 3), np.float32)
    img[:] = BG
    ground(img, V)
    on_tower = key['place'] == 'tower'
    shadows(img, V, horse_shadows(st_, dxh) + ([] if on_tower else duck_shadow(d, key)))
    tw = tower(V)
    over(img, tw)
    if on_tower:                                       # on the top book's cover, under the boots
        shadows(img, V, duck_shadow(d, key), clip=tw[..., 3:4])
    seat = key['place'] == 'seat'
    if on_tower:
        over(img, DUCK.render(V, d, (W, H)))
    elif seat:
        over(img, DUCK.render(V, d, (W, H), part='far'))
    hv = horse_view(V)
    hv.M = V @ D.T3(dxh, 0)
    over(img, GP.render_view(hv, st_))
    if key['place'] in ('air', 'lane'):
        over(img, DUCK.render(V, d, (W, H)))
    elif seat:
        over(img, DUCK.render(V, d, (W, H), part='near'))
    return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))


def cam_view(key):
    """The opening's framing: 1 opening unit = 1 frame px, camera at camX / camY."""
    k = 1 / PXU
    cx, cy = key['cam']
    return D.S3(k, k) @ D.T3(-wx(cx), -wy(cy))


def close_view(key, center=None, ppu=None):
    (u, v), s = key['close']
    u, v = center or (u, v)
    k = (ppu or s) / PXU
    return D.T3(W / 2, H / 2) @ D.S3(k, k) @ D.T3(-wx(u), -wy(v))


# ---------------------------------------------------------------- sheets
CELL_W, CELL_H, GAP, CAP = 960, 540, 16, 54
INK, GRAY = PV.INK, PV.GRAY
f_cap = PV.font(PV.FONT_MED, 30)
f_small = PV.font(PV.FONT_MED, 25)


def label(key):
    return f'{key["n"]}  {key["name"]}   T = {key["T"]:.2f} s'


def sheet(cells, title, path, notes=None):
    cols, rows = 2, 3
    Wt = cols * CELL_W + (cols + 1) * GAP
    Ht = 86 + rows * (CELL_H + CAP + GAP) + GAP
    S = Image.new('RGB', (Wt, Ht), (255, 255, 255))
    d = ImageDraw.Draw(S)
    d.text((GAP + 6, 22), title, font=PV.f_chip, fill=INK)
    for i in range(cols * rows):
        x, y = GAP + (i % cols) * (CELL_W + GAP), 86 + (i // cols) * (CELL_H + CAP + GAP)
        if i < len(cells):
            im, lab = cells[i]
            d.text((x + 4, y + 8), lab, font=f_cap, fill=INK)
            S.paste(im.resize((CELL_W, CELL_H), Image.LANCZOS), (x, y + CAP))
            d.rectangle((x, y + CAP, x + CELL_W - 1, y + CAP + CELL_H - 1), outline=(224, 218, 209), width=2)
        elif notes:
            for j, line in enumerate(notes):
                d.text((x + 10, y + CAP + 10 + j * 44), line, font=f_small, fill=GRAY)
    S.save(path)
    print(path, S.size)


NOTES = ['镜头＝开场的 camX / camY（1 开场单位＝1 px），',
         '浅色舞台、书堆为占位（开场的尺寸与配色）。',
         '鸭的姿态＝开场 duckPose 在该时刻的值；',
         '马＝horse-legs 的腿 / 尾 / 颈鬃 rig（预览时间 T − 1.9）。',
         '层级：书堆上鸭在马后；落下后在马前；',
         '骑乘时从鸭身中线分开，右半在马后、左半在马前。']


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--only', type=int, nargs='+', metavar='N', help='render only these keyframes (1-5), no sheets')
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    keys = [k for k in KEYS if not a.only or k['n'] in a.only]
    wide, close = [], []
    for key in keys:
        sc = scene(key)
        im = frame(key, cam_view(key), sc)
        p = os.path.join(OUT, f'kf{key["n"]}.png')
        im.save(p)
        print(p)
        ic = frame(key, close_view(key), sc)
        p = os.path.join(OUT, f'kf{key["n"]}-close.png')
        ic.save(p)
        print(p)
        wide.append((im, label(key)))
        close.append((ic, label(key)))
        if key['n'] == 5 and not a.only:
            iz = frame(key, close_view(key, (sc[2]['x'] / PXU, GROUND_V + (sc[2]['y'] - G.GROUND) / PXU - 40), 5.2), sc)
            p = os.path.join(OUT, 'kf5-seat.png')
            iz.save(p)
            print(p)
            close.append((iz, '5  骑乘放大：鸭身中线左右分层'))
    if not a.only:
        sheet(wide, '五个关键帧 · 开场镜头', os.path.join(OUT, 'keyframes-sheet.png'), NOTES)
        sheet(close, '五个关键帧 · 角色放大', os.path.join(OUT, 'keyframes-close-sheet.png'))


if __name__ == '__main__':
    main()
