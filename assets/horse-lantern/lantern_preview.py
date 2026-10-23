"""8 s 马灯 preview: the opening's lantern on the new horse, at night (same timeline as the gait preview).

Left: the whole horse (gait preview rig: legs, haunch, chain tail, neck/mane, body bob / pitch) in the desert
night - riders graded with the opening's nightGrade, the lamp, its pool on the sand and its bloom; the sand marks
scroll back at the horse's speed. The lamp has the softened swing: lantern.ts numbers, but it feels only 25 % of
the body's vertical jolts.
Right: two close-ups of the same frame - the opening's swing as it is and the softened one - and the swing angle
of both over the last 3 s.

Usage:
  python lantern_preview.py                       # -> <repo>/out/horse-lantern-preview.mp4 (ink lamp)
  python lantern_preview.py --still 1 3.4 6.2     # stills -> <repo>/out/horse-lantern-t1.png ...
  python lantern_preview.py --style svg           # the opening's vector lamp as it is (-> ...-svg.mp4 / .png)
  python lantern_preview.py --pivot 1225 1010     # another hanging point (2048 canvas px, body-local)
  python lantern_preview.py --jobs 2 --out my.mp4
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
sys.path.insert(1, os.path.join(os.path.dirname(HERE), 'horse-legs'))
import lantern as LT  # noqa: E402
import gait_preview as GP  # noqa: E402  (also puts horse-upper/motion on sys.path)

PV, R, GT, G = GP.PV, GP.R, GP.GT, GP.G
OUT = PV.OUT_DIR
FPS, DUR, NF = PV.FPS, PV.DUR, PV.NF
W, H = PV.W, PV.H
SET = dict(pivot=LT.PIVOT, style='ink')
SW = {}
PRE = 2.0  # s of run-in before T = 0 (the opening starts the lamp at rest under a walking horse)


def body(T):
    """Body-local canvas -> world canvas (bob / pitch), as in gait_preview.frame_state."""
    p = PV.params(T)
    return R.T3(0, p['bob'] / GP.NECK_BOB * GT.BOB_UNIT) @ R.R3(p['pitch'], *PV.CB)


def pivot_units(T):
    """World pivot in opening units: the horse runs forward by the ground scroll (canvas px / GT.UNIT)."""
    q = body(T) @ np.array([SET['pivot'][0], SET['pivot'][1], 1.0])
    return (GP.GAIT.scroll(T) + q[0]) / GT.UNIT, q[1] / GT.UNIT


def setup(pivot=None, style=None):
    if pivot is not None:
        SET['pivot'] = tuple(pivot)
    if style is not None:
        SET['style'] = style
    global VZ
    VZ = GP.View(ZK, (SET['pivot'][0] - TW / 2 / ZK, SET['pivot'][1] + 110 - TH_ / 2 / ZK), (0, 0), (TW, TH_))
    SW['open'] = LT.Swing(pivot_units, DUR + 0.5, pre=PRE)
    SW['soft'] = LT.Swing(pivot_units, DUR + 0.5, ky=LT.SOFT_KY, pre=PRE)


# ---------------------------------------------------------------- night colours (opening: desert_sky.png / sandG)
def hexf(h):
    return np.array(LT.rgb(h)[:3], np.float32)


SKY = [(0.0, '#090C1B'), (0.35, '#161C38'), (0.7, '#2A3258'), (0.92, '#4A5585'), (1.0, '#56628F')]
SAND = [(0.0, '#3A4982'), (0.04, '#37467E'), (0.09, '#2A376B'), (0.2, '#1B2450'), (1.0, '#0A0F27')]
SAND_LINE, SAND_MARK, SHADOW = hexf('#5A69A0'), hexf('#4A5890'), hexf('#04061A')


def ramp(stops, t):
    xs = [a for a, _ in stops]
    cols = np.stack([hexf(c) for _, c in stops])
    return np.stack([np.interp(t, xs, cols[:, i]) for i in range(3)], -1).astype(np.float32)


def backdrop(view, ground=True):
    """Night sky down to the ground line, moonlit sand under it (view px)."""
    w, h = view.size
    rows = np.arange(h, dtype=np.float32) + 0.5
    yg = view.M[1, 1] * G.GROUND + view.M[1, 2]
    if not ground:
        yg = max(yg, h * 1.6)  # close-ups: sky only, same gradient as the left view at that height
    col = np.where((rows < yg)[:, None], ramp(SKY, np.clip(rows / yg, 0, 1)),
                   ramp(SAND, np.clip((rows - yg) / max(1.0, H - yg), 0, 1)))
    return np.repeat(col[:, None, :], w, 1), yg


def sand(bg, view, st, yg, fl, cx):
    """Ground marks (scrolling), the lamp pool and soft contact shadows on the night sand."""
    k = view.k
    h, w = bg.shape[:2]
    S16 = 16.0
    ink = np.zeros((h, w), np.uint8)
    X = st['scroll']
    xw0, xw1 = (0 - view.M[0, 2]) / k, (w - view.M[0, 2]) / k
    n0, n1 = int(math.floor((xw0 + X) / GP.MARK_GAP)) - 1, int(math.ceil((xw1 + X) / GP.MARK_GAP)) + 1
    for n in range(n0, n1 + 1):
        xm = n * GP.MARK_GAP - X + 120 * GP.hashf(n, 1)
        ym = G.GROUND + 34 + 70 * GP.hashf(n, 2)
        ln = 50 + 90 * GP.hashf(n, 3)
        a0 = (int(round((view.M[0, 0] * xm + view.M[0, 2]) * S16)), int(round((view.M[1, 1] * ym + view.M[1, 2]) * S16)))
        a1 = (int(round((view.M[0, 0] * (xm + ln) + view.M[0, 2]) * S16)), a0[1])
        cv2.line(ink, a0, a1, 255, max(1, round(10 * k)), cv2.LINE_AA, 4)
    a = (ink.astype(np.float32) / 255)[..., None]
    bg[:] = bg * (1 - a) + SAND_MARK * a
    line = np.zeros((h, w), np.uint8)
    cv2.line(line, (0, int(round(yg * S16))), (w * 16, int(round(yg * S16))), 255, max(1, round(9 * k)), cv2.LINE_AA, 4)
    a = (line.astype(np.float32) / 255)[..., None]
    bg[:] = bg * (1 - a) + SAND_LINE * a
    surf, ctx = LT.surface(w, h)
    LT.pool(ctx, cx, yg, fl, LT.S * k)
    surf.flush()
    P = LT.to_rgba(surf)
    bg[:] = P[..., :3] + bg * (1 - P[..., 3:4])
    sh = np.zeros((h, w), np.uint8)

    def ell(x, y, ax, ay, val):
        cv2.ellipse(sh, (int(round((view.M[0, 0] * x + view.M[0, 2]) * S16)), int(round((view.M[1, 1] * y + view.M[1, 2]) * S16))),
                    (int(round(ax * k * S16)), int(round(ay * k * S16))), 0, 0, 360, int(val), -1, cv2.LINE_AA, 4)

    ell(1060, G.GROUND + 6, 1000, 44, 150)
    for key, q in st['legs'].items():
        Dm = GT.DIMS[key]
        toe = q['fet'] + GT.rot(Dm['toe'], q['a_hoof'])
        heel = q['fet'] + GT.rot(Dm['heel'], q['a_hoof'])
        av = GT.clamp(1 - (G.GROUND - max(toe[1], heel[1])) / 260, 0, 1)
        if av > 0:
            ell((toe[0] + heel[0]) / 2, G.GROUND + 4, 110 * (0.75 + 0.25 * av), 18, 255 * av)
    s = cv2.GaussianBlur(sh, (0, 0), max(1.0, 7 * k)).astype(np.float32)[..., None] / 255 * 0.45
    bg[:] = bg * (1 - s) + SHADOW * s


def scene(view, st, th, fl, ground=True):
    """One night view: backdrop (+ sand, pool, shadows), graded horse, lamp, bloom -> float RGB (view px)."""
    bg, yg = backdrop(view, ground)
    s = LT.S * view.k
    px, py = (view.M @ st['B'] @ np.array([SET['pivot'][0], SET['pivot'][1], 1.0]))[:2]
    cx, cy = LT.lamp_centre(px, py, th, s)
    if ground:
        sand(bg, view, st, yg, fl, cx)
    L = LT.night_grade(GP.render_view(view, st, tail=ground), s)
    img = L[..., :3] + bg * (1 - L[..., 3:4])
    surf, ctx = LT.surface(*view.size)
    LT.draw_lamp(ctx, px, py, th, fl, s, SET['style'])
    LT.bloom(ctx, cx, cy, fl, s)
    surf.flush()
    F = LT.to_rgba(surf)
    return F[..., :3] + img * (1 - F[..., 3:4])


# ---------------------------------------------------------------- layout
LEFT_W = 852
VL = GP.VL                                         # whole horse, as in the gait preview
CARD = PV.CARD
CW, CH = CARD[2] - CARD[0], CARD[3] - CARD[1]
TW, TH_, TY = 482, 548, 62                         # close-up tiles (card px)
TX = (22, CW - 22 - TW)
ZK = 0.5
VZ = None                                          # close-up view round the pivot (setup)
CHART_Y0, CHART_H = 690, 230                       # swing chart (card px): top, height
CHART_X0, CHART_X1, WIN, DEG = 118, CW - 34, 3.0, 75.0
TXT, CAP, DIM = (233, 236, 245), (160, 168, 196), (96, 104, 140)
ORANGE, OPEN_C, SOFT_C = (214, 116, 48), (240, 160, 90), (140, 190, 255)
CARD_BG, CARD_LINE = np.array([16, 21, 44], np.float32) / 255, (48, 57, 100)


def compose(T):
    st = GP.frame_state(T)
    fl = LT.flick(T)
    th_o, th_s = SW['open'](T), SW['soft'](T)
    img = np.empty((H, W, 3), np.float32)
    left = scene(VL, st, th_s, fl)
    img[:, :LEFT_W] = left
    img[:, LEFT_W:] = left[:, -1:]
    card = np.empty((CH, CW, 3), np.float32)
    card[:] = CARD_BG
    for x0, th in zip(TX, (th_o, th_s)):
        card[TY:TY + TH_, x0:x0 + TW] = scene(VZ, st, th, fl, ground=False)
    sub = img[CARD[1]:CARD[3], CARD[0]:CARD[2]]
    img[CARD[1]:CARD[3], CARD[0]:CARD[2]] = card * PV.card_mask + sub * (1 - PV.card_mask)
    out = Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))
    d = ImageDraw.Draw(out)
    d.rounded_rectangle(CARD, 22, outline=CARD_LINE, width=2)
    d.text((56, 30), '马灯预览（夜景）', font=PV.f_title, fill=TXT)
    x = 58
    for j, (name, a, b) in enumerate(PV.PHASES):
        on = a <= T < b
        tw = d.textlength(name, font=PV.f_chip)
        box = (x, 112, x + tw + 32, 156)
        if on:
            d.rounded_rectangle(box, 22, fill=ORANGE)
        else:
            d.rounded_rectangle(box, 22, outline=(70, 78, 112), width=2)
        d.text((x + 16, 114), name, font=PV.f_chip, fill=(255, 255, 255) if on else CAP)
        x = box[2] + 12
        if j < len(PV.PHASES) - 1:
            d.text((x, 114), '→', font=PV.f_chip, fill=DIM)
            x += 40
    d.text((58, 180), f'整体：柔化摆动（竖直颠簸 ×{LT.SOFT_KY:g}）' + ('，墨线版灯体' if SET['style'] == 'ink' else '，开场片原版灯体'),
           font=PV.f_cap, fill=CAP)
    cx, cy = CARD[:2]
    for x0, name, col in zip(TX, ('原参数（直接复用）', f'柔化（竖直颠簸 ×{LT.SOFT_KY:g}）'), (OPEN_C, SOFT_C)):
        d.rectangle((cx + x0, cy + TY, cx + x0 + TW - 1, cy + TY + TH_ - 1), outline=CARD_LINE, width=1)
        d.rounded_rectangle((cx + x0, cy + 18, cx + x0 + 14, cy + 32), 4, fill=col)
        d.text((cx + x0 + 24, cy + 12), name, font=PV.f_cap, fill=TXT)
    chart(d, T, cx, cy)
    d.text((cx + 22, cy + CH - 44), f'摆角  原参数 {math.degrees(th_o):+4.0f}°   柔化 {math.degrees(th_s):+4.0f}°      '
           f'火光 {fl:.2f}      挂点 ({SET["pivot"][0]:.0f}, {SET["pivot"][1]:.0f})', font=PV.f_cap, fill=CAP)
    d.rectangle((0, H - 6, W, H), fill=(36, 42, 72))
    d.rectangle((0, H - 6, int(W * T / DUR), H), fill=(214, 170, 130))
    return out


def chart(d, T, cx, cy):
    """Swing angle of both models over the last WIN seconds (+ = lamp toward the head), newest on the right."""
    x0, x1 = cx + CHART_X0, cx + CHART_X1
    yc = cy + CHART_Y0 + CHART_H / 2
    ys = lambda deg: yc - deg / DEG * CHART_H / 2  # noqa: E731
    xs = lambda t: x0 + (t - (T - WIN)) / WIN * (x1 - x0)  # noqa: E731
    d.text((cx + 22, cy + CHART_Y0 - 50), f'摆角（最近 {WIN:g} 秒，向上＝灯往前甩）', font=PV.f_cap, fill=CAP)
    d.rounded_rectangle((x0, cy + CHART_Y0, x1, cy + CHART_Y0 + CHART_H), 8, fill=(22, 28, 56))
    for deg, lab in ((60, '+60°'), (30, '+30°'), (0, '0°'), (-30, '−30°'), (-60, '−60°')):
        y = ys(deg)
        if deg == 0:
            d.line((x0, y, x1, y), fill=(76, 86, 124), width=2)
        else:
            for xx in range(int(x0), int(x1), 14):
                d.line((xx, y, min(xx + 6, x1), y), fill=(50, 58, 96), width=1)
        d.text((cx + 30, y - 14), lab, font=PV.f_cap, fill=DIM)
    lim = math.degrees(LT.TH_MAX)
    for sg in (1, -1):
        y = ys(sg * lim)
        for xx in range(int(x0), int(x1), 20):
            d.line((xx, y, min(xx + 10, x1), y), fill=(150, 80, 70), width=2)
    lab = f'限位 ±{lim:.0f}°'
    d.text((x1 - 14 - d.textlength(lab, font=PV.f_cap), ys(lim) - 38), lab, font=PV.f_cap, fill=(190, 110, 96))
    if T - WIN < PV.GS <= T:
        xg = xs(PV.GS)
        for yy in range(int(cy + CHART_Y0), int(cy + CHART_Y0 + CHART_H), 12):
            d.line((xg, yy, xg, yy + 6), fill=(120, 128, 160), width=2)
        d.text((xg + 6, cy + CHART_Y0 + CHART_H + 2), '起跑', font=PV.f_cap, fill=CAP)
    ts = np.arange(max(0.0, T - WIN), T + 1e-9, 1 / 120)
    if len(ts) > 1:
        for key, col in (('open', OPEN_C), ('soft', SOFT_C)):
            pts = [(xs(t), ys(math.degrees(SW[key](t)))) for t in ts]
            d.line(pts, fill=col, width=3, joint='curve')
    d.line((x1, cy + CHART_Y0, x1, cy + CHART_Y0 + CHART_H), fill=TXT, width=2)


def frame_bytes(i):
    return np.asarray(compose(i / FPS)).tobytes()


def init(pivot, style, haunch):
    GP.set_haunch(haunch)
    setup(pivot, style)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--still', type=float, nargs='+', metavar='T', help='render stills at these times (s) instead of the video')
    ap.add_argument('--style', choices=('ink', 'svg'), default='ink',
                    help="lamp body: this pack's ink outline (ink, default) or the opening's vector lamp (svg)")
    ap.add_argument('--pivot', type=float, nargs=2, metavar=('X', 'Y'), help='hanging point, 2048 canvas px (body-local)')
    ap.add_argument('--jobs', type=int, default=2, help='worker processes (default 2)')
    ap.add_argument('--out', help='output .mp4 (default out/horse-lantern-preview.mp4)')
    a = ap.parse_args()
    pivot = tuple(a.pivot) if a.pivot else LT.PIVOT
    init(pivot, a.style, True)
    tag = '-svg' if a.style == 'svg' else ''
    os.makedirs(OUT, exist_ok=True)
    if a.still:
        for t in a.still:
            p = os.path.join(OUT, f'horse-lantern{tag}-t{t:g}.png')
            compose(t).save(p)
            print(p)
        return
    out = a.out or os.path.join(OUT, f'horse-lantern-preview{tag}.mp4')
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
    with Pool(max(1, a.jobs), initializer=init, initargs=(pivot, a.style, True)) as pool:
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
