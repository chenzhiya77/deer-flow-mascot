"""8 s leg gait preview: walk -> head toss + take-off -> gallop (same timeline as the neck/mane and tail previews).

Left: the whole horse (legs + chain tail + neck/mane rig, body bob / pitch) on ground that scrolls back at
the horse's speed - a planted hoof has to move exactly with the ground marks. Right: a legs close-up of
the same frame and a footfall chart of the last 3 s (bar = hoof on the ground). The near hind thigh drawn
on the body turns with the near hind upper leg, and where that leg is behind the body the body's outline
is drawn thinner (haunch.py).

Usage:
  python gait_preview.py                     # -> <repo>/out/horse-gait-preview.mp4
  python gait_preview.py --still 1.0 5.2     # stills -> <repo>/out/horse-gait-t1.0.png ...
  python gait_preview.py --jobs 2 --out my.mp4
  python gait_preview.py --no-haunch         # thigh kept still, for comparison (-> ...-no-haunch.mp4 / .png)
  python gait_preview.py --no-seam           # full-weight outline over the near hind leg (-> ...-no-seam.mp4)
"""
import argparse
import math
import os
import shutil
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tail_preview as TP  # noqa: E402  (tail motion; also puts horse-upper/motion on sys.path)
import gait as GT  # noqa: E402
import gen as G  # noqa: E402
import haunch as HN  # noqa: E402  (near hind thigh on the body follows the LH upper leg)
import parts as P  # noqa: E402
import preview as PV  # noqa: E402  (neck/mane preview: timeline, params, fonts)
import rig as R  # noqa: E402
import tailrig as TR  # noqa: E402

OUT = PV.OUT_DIR
FPS, DUR, NF = PV.FPS, PV.DUR, PV.NF
W, H = PV.W, PV.H
NECK_BOB = 5.8  # canvas px per opening unit of params()['bob'] in the neck/mane preview (no legs there)

# gait on the preview timeline: stride phase from the neck/mane preview, ground scroll = integral of speed
_g = np.array([PV.gblend(i * PV.DT) for i in range(PV.NS)])
_v = np.array([PV.speed(i * PV.DT) for i in range(PV.NS)]) * GT.UNIT
GAIT = GT.Gait(PV.PHI, _g, np.concatenate([[0.0], np.cumsum((_v[1:] + _v[:-1]) / 2 * PV.DT)]), PV.DT)
MAN = G.load_manifest()
LEG_PARTS = ('upper', 'lower', 'hoof')
HAUNCH = True  # --no-haunch: keep the drawn near hind thigh still
SEAM = True    # --no-seam: keep the full body outline over the near hind leg


def set_haunch(on):
    global HAUNCH
    HAUNCH = on


def set_seam(on):
    global SEAM
    SEAM = on


def set_flags(haunch, seam):
    set_haunch(haunch)
    set_seam(seam)


def T3(tx, ty):
    return np.array([[1, 0, tx], [0, 1, ty], [0, 0, 1.]])


def S3(sx, sy):
    return np.diag([sx, sy, 1.])


def Rot3(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.]])


HALF = T3(0.5, 0.5)    # pixel index -> continuous coordinate (pixel i spans [i, i + 1))
UNHALF = T3(-0.5, -0.5)


def premul_png(path):
    a = np.asarray(Image.open(path).convert('RGBA'), np.float32) / 255
    return np.concatenate([a[..., :3] * a[..., 3:4], a[..., 3:4]], 2)


class View:
    """World (canvas, continuous) -> layer px: x = off + k (X - origin). Pieces are pre-scaled to k."""

    def __init__(self, k, origin, off, size):
        self.k, self.size = k, size
        self.M = np.array([[k, 0, off[0] - origin[0] * k], [0, k, off[1] - origin[1] * k], [0, 0, 1.]])
        self.pieces = {}
        for name, m in MAN.items():
            if name == 'tail':
                continue
            pm = premul_png(os.path.join(G.OUT, m['file']))
            h, w = pm.shape[:2]
            sw, sh = max(1, round(w * k)), max(1, round(h * k))
            small = cv2.resize(pm, (sw, sh), interpolation=cv2.INTER_AREA)
            # small index -> piece continuous coordinate (pivots are continuous)
            self.pieces[name] = (small, S3(w / sw, h / sh) @ HALF, m['pivot'])
        self.bust_wh = (round(R.FW * k / R.RS), round(R.FH * k / R.RS))
        # bust frame index -> canvas: continuous frame px / RS + frame origin
        self.bust_A = T3(R.FX0, R.FY0) @ S3(1 / R.RS, 1 / R.RS) @ S3(R.FW / self.bust_wh[0], R.FH / self.bust_wh[1]) @ HALF

    def y(self, Y):
        return self.M[1, 1] * Y + self.M[1, 2] - 0.5   # layer row index of world Y

    def x(self, X):
        return self.M[0, 0] * X + self.M[0, 2] - 0.5


def put(layer, src, A, keep=None):
    """Composite premultiplied src into layer through A (3x3: src index -> layer index), bbox-limited.
    keep: optional layer-sized map the warped src is multiplied by first (1 = all of it)."""
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


def put_piece(view, layer, name, target, ang, s=1.0):
    small, idx2q, piv = view.pieces[name]
    A = UNHALF @ view.M @ T3(*target) @ Rot3(ang) @ S3(1.0, s) @ T3(-piv[0], -piv[1]) @ idx2q
    put(layer, small, A)


TAIL_BOX = (-860, 700, 680, 2260)  # body-local canvas box the tail stays in


def seam_view(view, st):
    """haunch.seam() band of this frame in view px (layer-sized), placed like the bust."""
    band = st['seam']
    bh, bw = band.shape
    sw, sh = max(1, round(bw * view.k / R.RS)), max(1, round(bh * view.k / R.RS))
    small = cv2.resize(band, (sw, sh), interpolation=cv2.INTER_AREA)
    A = (UNHALF @ view.M @ st['B'] @ T3(R.FX0, R.FY0) @ S3(1 / R.RS, 1 / R.RS) @ T3(HN.FX0, HN.FY0)
         @ S3(bw / sw, bh / sh) @ HALF)
    return cv2.warpAffine(small, A[:2], view.size, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)


def render_view(view, st, tail=True):
    """Premultiplied RGBA layer of the horse in this view: tail, far legs, near hind leg, bust, near fore leg.
    Where the near hind leg is behind the bust, the outer band of the body outline (st['seam']) is left out,
    so the joint line at the thigh is thinner than the silhouette (as in the reference)."""
    w, h = view.size
    layer = np.zeros((h, w, 4), np.float32)
    k, B = view.k, st['B']
    if tail:
        tw, th = round((TAIL_BOX[2] - TAIL_BOX[0]) * k), round((TAIL_BOX[3] - TAIL_BOX[1]) * k)
        tl = TP.RIG.render(st['spine'], P.TAIL_PIVOT, TAIL_BOX[:2], (tw, th), scale=k)
        put(layer, tl, UNHALF @ view.M @ B @ T3(*TAIL_BOX[:2]) @ S3(1 / k, 1 / k) @ HALF)
    keep = None
    for key in ('RH', 'RF', 'LH', 'BUST', 'LF'):
        if key == 'BUST':
            small = cv2.resize(st['fr'], view.bust_wh, interpolation=cv2.INTER_AREA)
            put(layer, small, UNHALF @ view.M @ B @ view.bust_A, keep)
            continue
        q, pre = st['legs'][key], key.lower()
        own = key == 'LH' and st.get('seam') is not None   # near hind leg on its own layer: its alpha is needed
        dst = np.zeros_like(layer) if own else layer
        put_piece(view, dst, pre + '_upper', q['hip'], q['a_up'], q['s'])
        put_piece(view, dst, pre + '_lower', q['knee'], q['a_low'], q['s'])
        put_piece(view, dst, pre + '_hoof', q['fet'], q['a_hoof'])
        if own:
            layer *= 1 - dst[..., 3:4]
            layer += dst
            keep = 1 - seam_view(view, st) * dst[..., 3]
    return layer


GROUND_LINE = np.array([186, 176, 162], np.float32) / 255
GROUND_MARK = np.array([206, 197, 185], np.float32) / 255
GROUND_FILL = np.array([238, 234, 227], np.float32) / 255
MARK_GAP = 800.0  # canvas px between ground marks: well over twice a gallop frame's scroll (266 px at 30 fps)


def hashf(n, salt):
    return ((int(n) * 2654435761 + salt * 40503) % 4294967296) / 4294967296


def ground(bg, view, st):
    """Ground under the horse in view coordinates, drawn into bg (float RGB, the view's size): fill, line,
    scrolling marks and soft contact shadows."""
    k = view.k
    yg = view.y(G.GROUND)
    h, w = bg.shape[:2]
    y0 = max(0, int(yg - 80 * k / 0.25))
    band = bg[y0:]
    # fill under the line, fading out toward the bottom of the view
    t = np.clip((np.arange(y0, h, dtype=np.float32) - yg) / max(1.0, h - yg), 0, 1)
    fa = np.where(np.arange(y0, h) >= yg + 0.5, 1 - t * t, 0.0).astype(np.float32)[:, None, None]
    band[:] = band * (1 - fa) + GROUND_FILL * fa
    sh = np.zeros(band.shape[:2], np.uint8)
    ink = np.zeros(band.shape[:2], np.uint8)
    S16 = 16.0

    def ell(cx, cy, ax, ay, val):
        cv2.ellipse(sh, (int(round(view.x(cx) * S16)), int(round((view.y(cy) - y0) * S16))),
                    (int(round(ax * k * S16)), int(round(ay * k * S16))), 0, 0, 360, int(val), -1, cv2.LINE_AA, 4)

    ell(1060, G.GROUND + 6, 1000, 44, 120)
    for key, q in st['legs'].items():
        Dm = GT.DIMS[key]
        toe = q['fet'] + GT.rot(Dm['toe'], q['a_hoof'])
        heel = q['fet'] + GT.rot(Dm['heel'], q['a_hoof'])
        hgt = G.GROUND - max(toe[1], heel[1])
        a = GT.clamp(1 - hgt / 260, 0, 1)
        if a > 0:
            ell((toe[0] + heel[0]) / 2, G.GROUND + 4, 110 * (0.75 + 0.25 * a), 18, 255 * a)
    sh = cv2.GaussianBlur(sh, (0, 0), max(1.0, 7 * k)).astype(np.float32) / 255
    band *= (1 - 0.2 * sh)[..., None]
    # line + marks (marks keep their identity while they scroll: index n of the mark in ground coordinates)
    cv2.line(ink, (0, int(round((yg - y0) * S16))), (w * 16, int(round((yg - y0) * S16))), 255,
             max(1, round(9 * k)), cv2.LINE_AA, 4)
    X = st['scroll']
    xw0, xw1 = (0 - view.M[0, 2]) / k, (w - view.M[0, 2]) / k
    n0, n1 = int(math.floor((xw0 + X) / MARK_GAP)) - 1, int(math.ceil((xw1 + X) / MARK_GAP)) + 1
    marks = np.zeros_like(ink)
    for n in range(n0, n1 + 1):
        xm = n * MARK_GAP - X + 120 * hashf(n, 1)
        ym = G.GROUND + 34 + 70 * hashf(n, 2)
        ln = 50 + 90 * hashf(n, 3)
        a0 = (int(round(view.x(xm) * S16)), int(round((view.y(ym) - y0) * S16)))
        a1 = (int(round(view.x(xm + ln) * S16)), a0[1])
        cv2.line(marks, a0, a1, 255, max(1, round(10 * k)), cv2.LINE_AA, 4)
    for m, col in ((marks, GROUND_MARK), (ink, GROUND_LINE)):
        a = (m.astype(np.float32) / 255)[..., None]
        band[:] = band * (1 - a) + col * a
    return bg


# ---------------------------------------------------------------- layout
LEFT_W = 852
VL = View(0.24, (-680, -120), (20, 310), (LEFT_W, H))          # whole horse
CARD = PV.CARD
CW, CH = CARD[2] - CARD[0], CARD[3] - CARD[1]
ZTOP, ZH = 58, 520                                              # close-up band inside the card
VZ = View(0.42, (-228, 1490), (0, 0), (CW, ZH))                 # legs close-up
FADE = 40                                                       # px: close-up fades in at its top edge
CHART_Y, ROW_H, ROW_GAP = 650, 34, 22                           # footfall chart (card px)
CHART_X0, CHART_X1, WIN = 118, CW - 34, 3.0
ROWS = [('LF', '左前'), ('RF', '右前'), ('LH', '左后'), ('RH', '右后')]
BAR = dict(LF=(214, 116, 48), LH=(214, 116, 48), RF=(232, 177, 128), RH=(232, 177, 128))
INK, GRAY, ORANGE = PV.INK, PV.GRAY, PV.ORANGE
_fade = np.clip(np.arange(ZH, dtype=np.float32) / FADE, 0, 1)[:, None, None]


def frame_state(T):
    p = PV.params(T)
    B = R.T3(0, p['bob'] / NECK_BOB * GT.BOB_UNIT) @ R.R3(p['pitch'], *PV.CB)
    legs = GT.poses(GAIT, T, p['g'], B)
    th = HN.angle(legs, p['pitch']) if HAUNCH else 0.0
    mp = HN.maps(th)
    return dict(p=p, B=B, legs=legs, haunch=th, scroll=GAIT.scroll(T),
                spine=TR.chain_spine(TP.tail_dev(T), TP.L, G.TAIL_AXIS, G.SPINE_N),
                fr=R.render(p['neck'], p['head'], p['blocks'], p['hair'], front=HN.front(th, mp)),
                seam=HN.seam(th, mp) if SEAM else None)


def compose(T):
    st = frame_state(T)
    img = np.empty((H, W, 3), np.float32)
    img[:] = PV.BG
    left = img[:, :LEFT_W]
    ground(left, VL, st)
    Lh = render_view(VL, st)
    left[:] = Lh[..., :3] + left * (1 - Lh[..., 3:4])
    # card: white, legs close-up band, footfall chart drawn on top later
    card = np.ones((CH, CW, 3), np.float32)
    zb = card[ZTOP:ZTOP + ZH]
    ground(zb, VZ, st)
    Z = render_view(VZ, st, tail=False) * _fade  # legs only: no tail tip poking in at the edge
    zb[:] = Z[..., :3] + zb * (1 - Z[..., 3:4])
    sub = img[CARD[1]:CARD[3], CARD[0]:CARD[2]]
    img[CARD[1]:CARD[3], CARD[0]:CARD[2]] = card * PV.card_mask + sub * (1 - PV.card_mask)
    out = Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))
    d = ImageDraw.Draw(out)
    d.rounded_rectangle(CARD, 22, outline=(224, 218, 209), width=2)
    d.text((56, 30), '腿的步态预览', font=PV.f_title, fill=INK)
    x = 58
    for j, (name, a, b) in enumerate(PV.PHASES):
        on = a <= T < b
        tw = d.textlength(name, font=PV.f_chip)
        box = (x, 112, x + tw + 32, 156)
        if on:
            d.rounded_rectangle(box, 22, fill=ORANGE)
        else:
            d.rounded_rectangle(box, 22, outline=(214, 207, 198), width=2)
        d.text((x + 16, 114), name, font=PV.f_chip, fill=(255, 255, 255) if on else GRAY)
        x = box[2] + 12
        if j < len(PV.PHASES) - 1:
            d.text((x, 114), '→', font=PV.f_chip, fill=(190, 183, 175))
            x += 40
    d.text((58, 180), '整体（地面按马速后移，着地的蹄子应跟着地面标记走）', font=PV.f_cap, fill=GRAY)
    cx, cy = CARD[:2]
    d.text((cx + 22, cy + 16), '腿部放大', font=PV.f_cap, fill=GRAY)
    footfall(d, T, cx, cy)
    g = st['p']['g']
    _, beta, S = GT.law('LF', 0.0, g)
    rate = PV.speed(T) * beta / GT.lerp(GT.GAIT['walk']['S'], GT.GAIT['gallop']['S'], g)
    d.text((cx + 22, cy + CH - 44), f'步幅 {S:.0f} px   着地占比 {beta:.0%}   每步 {1 / rate:.2f} 秒   腿拉伸 '
           f'{max(q["s"] for q in st["legs"].values()) - 1:.0%}   臀部 {st["haunch"]:+.0f}°', font=PV.f_cap, fill=GRAY)
    d.rectangle((0, H - 6, W, H), fill=(232, 227, 219))
    d.rectangle((0, H - 6, int(W * T / DUR), H), fill=(214, 170, 130))
    return out


def footfall(d, T, cx, cy):
    """Stance bars of the last WIN seconds, newest on the right."""
    d.text((cx + 22, cy + CHART_Y - 46), f'着地时序（最近 {WIN:g} 秒，色条＝蹄子着地）', font=PV.f_cap, fill=GRAY)
    xs = lambda t: cx + CHART_X0 + (t - (T - WIN)) / WIN * (CHART_X1 - CHART_X0)  # noqa: E731
    for r, (key, label) in enumerate(ROWS):
        y = cy + CHART_Y + r * (ROW_H + ROW_GAP)
        d.text((cx + 30, y + 1), label, font=PV.f_cap, fill=GRAY)
        d.rounded_rectangle((cx + CHART_X0, y, cx + CHART_X1, y + ROW_H), 8, fill=(244, 240, 234))
        for a, b in GAIT.stance_runs(key, max(0.0, T - WIN), T):
            x0, x1 = xs(max(a, T - WIN, 0.0)), xs(min(b, T))
            if x1 - x0 >= 1:
                d.rounded_rectangle((x0, y, x1, y + ROW_H), 8, fill=BAR[key])
    if T - WIN < PV.GS <= T:
        xg = xs(PV.GS)
        y0, y1 = cy + CHART_Y - 8, cy + CHART_Y + 4 * ROW_H + 3 * ROW_GAP + 8
        for yy in range(int(y0), int(y1), 12):
            d.line((xg, yy, xg, min(yy + 6, y1)), fill=(160, 152, 144), width=2)
        d.text((xg + 6, y1 - 2), '起跑', font=PV.f_cap, fill=GRAY)
    d.line((cx + CHART_X1, cy + CHART_Y - 8, cx + CHART_X1, cy + CHART_Y + 4 * ROW_H + 3 * ROW_GAP + 8), fill=INK, width=2)


def frame_bytes(i):
    return np.asarray(compose(i / FPS)).tobytes()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--still', type=float, nargs='+', metavar='T', help='render stills at these times (s) instead of the video')
    ap.add_argument('--jobs', type=int, default=2, help='worker processes (default 2)')
    ap.add_argument('--out', help='output .mp4 (default out/horse-gait-preview.mp4)')
    ap.add_argument('--no-haunch', action='store_true', help='keep the drawn near hind thigh still (comparison)')
    ap.add_argument('--no-seam', action='store_true', help='keep the full body outline over the near hind leg (comparison)')
    a = ap.parse_args()
    set_haunch(not a.no_haunch)
    set_seam(not a.no_seam)
    tag = ('-no-haunch' if a.no_haunch else '') + ('-no-seam' if a.no_seam else '')
    os.makedirs(OUT, exist_ok=True)
    if a.still:
        for t in a.still:
            p = os.path.join(OUT, f'horse-gait{tag}-t{t:g}.png')
            compose(t).save(p)
            print(p)
        return
    out = a.out or os.path.join(OUT, f'horse-gait-preview{tag}.mp4')
    ff = shutil.which('ffmpeg')
    if ff:
        enc = subprocess.Popen([ff, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                                '-framerate', str(FPS), '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18',
                                '-preset', 'slow', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
        write = enc.stdin.write
    else:
        print('ffmpeg not found: using OpenCV mp4v (lower quality)', file=sys.stderr)
        vw = cv2.VideoWriter(out, cv2.VideoWriter_fourcc(*'mp4v'), FPS, (W, H))

        def write(buf):
            vw.write(cv2.cvtColor(np.frombuffer(buf, np.uint8).reshape(H, W, 3), cv2.COLOR_RGB2BGR))
    from multiprocessing import Pool
    with Pool(max(1, a.jobs), initializer=set_flags, initargs=(HAUNCH, SEAM)) as pool:  # flags also under spawn
        for n, buf in enumerate(pool.imap(frame_bytes, range(NF))):
            write(buf)
            if n % 30 == 0:
                print(f'{n}/{NF}', flush=True)
    if ff:
        enc.stdin.close()
        if enc.wait():
            sys.exit('ffmpeg failed')
    else:
        vw.release()
    print(out)


if __name__ == '__main__':
    main()
