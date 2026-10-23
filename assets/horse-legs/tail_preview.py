"""8 s tail swing preview: walk -> head toss + take-off -> gallop (same timeline as the neck/mane preview).

Left: whole horse (neck/mane rig + chain tail) with body bob / pitch. Right: tail close-up, body fixed.
Legs are left out, like the neck/mane preview; gait_preview.py adds them.

Usage:
  python tail_preview.py                     # -> <repo>/out/horse-tail-preview.mp4
  python tail_preview.py --still 1.0 5.2     # stills -> <repo>/out/horse-tail-t1.0.png ...
  python tail_preview.py --jobs 2 --out my.mp4
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
MOTION = os.path.join(os.path.dirname(HERE), 'horse-upper', 'motion')  # neck/mane rig + its preview timeline
sys.path.insert(0, HERE)
sys.path.insert(1, MOTION)
import gen as G  # noqa: E402
import parts as P  # noqa: E402
import preview as PV  # noqa: E402  (neck/mane preview: timeline, params, fonts)
import rig as R  # noqa: E402
import tailrig as TR  # noqa: E402

OUT = PV.OUT_DIR  # <repo>/out
FPS, DUR, NF = PV.FPS, PV.DUR, PV.NF
W, H = PV.W, PV.H
SPINE_N = G.SPINE_N

RIG = G.tail_rig(G.load_manifest())
L = RIG.length
MO = TR.MOTION

# tail wave phase, integrated so frequency changes never chirp
PSI_T = np.zeros(PV.NS)
_p = 0.0
for _i in range(PV.NS):
    PSI_T[_i] = _p
    _p += 2 * math.pi * TR.lerp(*MO['freq'], PV.gblend(_i * PV.DT)) * PV.DT


def tail_dev(T):
    psi = PV.samp(PSI_T, T)
    gs = [PV.gblend(T - MO['follow'] * i) for i in range(TR.NSEG)]
    return TR.chain_dev(psi, gs, L)


# ---------------------------------------------------------------- layout
SL = 0.245                                   # whole-horse panel: video px per canvas px
BX0, BY0, BX1, BY1 = -680, -120, 2700, 2100  # body-local layer (canvas)
LW, LH = round((BX1 - BX0) * SL), round((BY1 - BY0) * SL)
OFFL = (24, 380)                             # video px of canvas (BX0, BY0)
C2V = np.array([[SL, 0, OFFL[0] - BX0 * SL], [0, SL, OFFL[1] - BY0 * SL], [0, 0, 1.]])
L2C = np.array([[1 / SL, 0, BX0], [0, 1 / SL, BY0], [0, 0, 1.]])
SW, SH = round(R.FW * SL / R.RS), round(R.FH * SL / R.RS)
SM2L = np.array([[R.FW / SW / R.RS * SL, 0, (R.FX0 - BX0) * SL], [0, R.FH / SH / R.RS * SL, (R.FY0 - BY0) * SL]])
CARD = PV.CARD
CW, CH = CARD[2] - CARD[0], CARD[3] - CARD[1]
SR, ZX0, ZY0 = 0.62, -660, 700               # close-up: scale, canvas origin
ZM = np.array([[SR, 0, -ZX0 * SR], [0, SR, -ZY0 * SR], [0, 0, 1.]]) @ PV.F2C
INK, GRAY, ORANGE = PV.INK, PV.GRAY, PV.ORANGE
PHASES = PV.PHASES


def over(dst, src):
    dst *= (1 - src[..., 3:4])
    dst += src
    return dst


def compose(T):
    p = PV.params(T)
    dev = tail_dev(T)
    spine = TR.chain_spine(dev, L, G.TAIL_AXIS, SPINE_N)
    fr = R.render(p['neck'], p['head'], p['blocks'], p['hair'])  # premultiplied, body-local, RS scale
    img = np.empty((H, W, 3), np.float32)
    img[:] = PV.BG
    # whole horse: tail behind the bust, then body bob / pitch
    layer = RIG.render(spine, P.TAIL_PIVOT, (BX0, BY0), (LW, LH), scale=SL)
    small = cv2.resize(fr, (SW, SH), interpolation=cv2.INTER_AREA)
    over(layer, cv2.warpAffine(small, SM2L, (LW, LH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0)))
    M = C2V @ R.T3(0, p['bob']) @ R.R3(p['pitch'], *PV.CB) @ L2C
    Lv = cv2.warpAffine(layer, M[:2], (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    img = Lv[..., :3] + img * (1 - Lv[..., 3:4])
    # close-up card (body fixed)
    Z = RIG.render(spine, P.TAIL_PIVOT, (ZX0, ZY0), (CW, CH), scale=SR)
    over(Z, cv2.warpAffine(fr, ZM[:2], (CW, CH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0)))
    card = Z[..., :3] + np.ones((CH, CW, 3), np.float32) * (1 - Z[..., 3:4])
    sub = img[CARD[1]:CARD[3], CARD[0]:CARD[2]]
    img[CARD[1]:CARD[3], CARD[0]:CARD[2]] = card * PV.card_mask + sub * (1 - PV.card_mask)
    out = Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))
    d = ImageDraw.Draw(out)
    d.rounded_rectangle(CARD, 22, outline=(224, 218, 209), width=2)
    d.text((56, 30), '尾巴摆动预览', font=PV.f_title, fill=INK)
    x = 58
    for j, (name, a, b) in enumerate(PHASES):
        on = a <= T < b
        tw = d.textlength(name, font=PV.f_chip)
        box = (x, 112, x + tw + 32, 156)
        if on:
            d.rounded_rectangle(box, 22, fill=ORANGE)
        else:
            d.rounded_rectangle(box, 22, outline=(214, 207, 198), width=2)
        d.text((x + 16, 114), name, font=PV.f_chip, fill=(255, 255, 255) if on else GRAY)
        x = box[2] + 12
        if j < len(PHASES) - 1:
            d.text((x, 114), '→', font=PV.f_chip, fill=(190, 183, 175))
            x += 40
    d.text((58, 180), '整体（身体随步态起伏；腿的步态见 gait_preview.py）', font=PV.f_cap, fill=GRAY)
    d.text((CARD[0] + 22, CARD[1] + 16), '尾巴局部（身体固定）', font=PV.f_cap, fill=GRAY)
    g = PV.gblend(T)
    hz = TR.lerp(*MO['freq'], g)
    d.text((CARD[0] + 22, CARD[3] - 44), f'尾根 {dev[0]:+.0f}°   尾梢 {dev[-1]:+.0f}°   甩动 {hz:.1f} 次/秒', font=PV.f_cap, fill=GRAY)
    d.rectangle((0, H - 6, W, H), fill=(232, 227, 219))
    d.rectangle((0, H - 6, int(W * T / DUR), H), fill=(214, 170, 130))
    return out


def frame_bytes(i):
    return np.asarray(compose(i / FPS)).tobytes()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--still', type=float, nargs='+', metavar='T', help='render stills at these times (s) instead of the video')
    ap.add_argument('--jobs', type=int, default=2, help='worker processes (default 2)')
    ap.add_argument('--out', help='output .mp4 (default out/horse-tail-preview.mp4)')
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    if a.still:
        for t in a.still:
            p = os.path.join(OUT, f'horse-tail-t{t:g}.png')
            compose(t).save(p)
            print(p)
        return
    out = a.out or os.path.join(OUT, 'horse-tail-preview.mp4')
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
    with Pool(max(1, a.jobs)) as pool:
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
