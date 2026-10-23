"""8 s neck + mane swing preview: walk -> head toss + take-off -> gallop.

Left: the whole horse with body bob / pitch. Right: body-local zoom card
(body fixed) to check the neck junctions. Timing follows the opening film's
mount / gait timeline, shifted 1.9 s earlier.

Usage:
  python preview.py                      # -> <repo>/out/horse-neck-mane-preview.mp4
  python preview.py --still 1.0 3.8      # stills -> <repo>/out/horse-neck-mane-t1.0.png ...
  python preview.py --jobs 4 --out my.mp4

Encodes with ffmpeg (libx264, crf 18) when it is on PATH, else falls back to
OpenCV's mp4v writer.
"""

import argparse
import math
import os
import shutil
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig as R  # noqa: E402

REPO = os.path.dirname(R.ASSETS)
OUT_DIR = os.path.join(REPO, 'out')

FPS, DUR = 30, 8.0
NF = int(DUR * FPS)
T_TOSS, GS, GE = 3.05, 3.10, 3.85            # head toss (mount + 0.05) / gait start / gait end
def clamp(x, a, b): return max(a, min(b, x))
def smooth(a, b, x): t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def lerp(a, b, t): return a + (b - a) * t
def ring(t, f, d): return 0.0 if t < 0 else math.exp(-d * t) * math.sin(2 * math.pi * f * t)
def toss(T): return -9 * ring(T - T_TOSS, 1.8, 4)
def gblend(T): return smooth(GS, GS + 0.55, T)          # 0 = walk, 1 = gallop
def speed(T): return lerp(349, 1400, smooth(GS, GE, T))


# stride phase phi and mane-wave phase psi are integrated, so rate changes never chirp
DT = 1 / 600
NS = int((DUR + 1) / DT) + 2
PHI = np.zeros(NS); PSI = np.zeros(NS)
_phi, _psi = 0.18, 0.0
for _i in range(NS):
    _T = _i * DT; PHI[_i] = _phi; PSI[_i] = _psi
    _g = gblend(_T)
    _phi += speed(_T) * lerp(0.62, 0.32, _g) / lerp(140, 150, _g) * DT
    _psi += 2 * math.pi * lerp(1.1, 2.6, _g) * 0.9 * DT
def samp(a, T): f = T / DT; i = int(f); return a[i] + (a[i + 1] - a[i]) * (f - i)


def params(T):
    """Pose at time T (degrees; bob in 2048-canvas px)."""
    phi, psi, g = samp(PHI, T), samp(PSI, T), gblend(T)
    neck = lerp(3.2 * math.sin(4 * math.pi * phi + 0.7), 6.5 * math.sin(2 * math.pi * (phi + 0.12)), g) + toss(T)
    bob = lerp(2.6 * math.cos(4 * math.pi * phi), -11 * math.cos(2 * math.pi * (phi - 0.95)), g)
    pitch = lerp(1.0 * math.sin(4 * math.pi * phi), -4.6 * math.sin(2 * math.pi * (phi + 0.03)), g)
    amp, bias = lerp(2, 5.5, g), lerp(0.5, 5.5, g)
    blocks = [bias + amp * math.sin(psi - 0.9 * i) - 0.5 * toss(T - 0.05 * i) for i in range(6)]
    hair = lerp(0, -2.5, g) + lerp(2.5, 5, g) * math.sin(1.1 * psi + 0.6) - 0.5 * toss(T - 0.04)
    return dict(neck=neck, head=0.6 * toss(T), bob=bob * 5.8, pitch=pitch, blocks=blocks, hair=hair, g=g)


# ---------------------------------------------------------------- layout
W, H = 1920, 1080
BG = np.array([247, 245, 240], np.float32) / 255
SL, ORIG, OFFL = 0.30, (71, -93), (50, 380)  # whole-horse panel: canvas scale / canvas origin / video px
CB = (1049, 1500)                            # body pitch pivot (canvas)
CARD = (860, 36, 1890, 1046)                 # zoom card (video px)
ZX0, ZY0 = 1000, -200                        # zoom region origin (canvas)
SR = (CARD[2] - CARD[0]) / 1720
F2C = np.array([[1 / R.RS, 0, R.FX0], [0, 1 / R.RS, R.FY0], [0, 0, 1.]])
k = SL / R.RS
SW, SH = round(R.FW * k), round(R.FH * k)
S_INV = np.diag([R.FW / SW, R.FH / SH, 1.])
C2V = np.array([[SL, 0, OFFL[0] - ORIG[0] * SL], [0, SL, OFFL[1] - ORIG[1] * SL], [0, 0, 1.]])
CW, CH = CARD[2] - CARD[0], CARD[3] - CARD[1]
ZM = np.array([[SR, 0, -ZX0 * SR], [0, SR, -ZY0 * SR], [0, 0, 1.]]) @ F2C
card_mask = Image.new('L', (CW, CH), 0)
ImageDraw.Draw(card_mask).rounded_rectangle((0, 0, CW - 1, CH - 1), 22, fill=255)
card_mask = np.array(card_mask, np.float32)[..., None] / 255

FONT_DIRS = ['C:/Windows/Fonts', '/System/Library/Fonts', '/usr/share/fonts/google-noto-cjk',
             '/usr/share/fonts/opentype/noto', '/usr/share/fonts/noto-cjk']
FONT_BOLD = ['msyhbd.ttc', 'PingFang.ttc', 'NotoSansSC-Bold.otf', 'NotoSansCJK-Bold.ttc']
FONT_MED = ['msyh.ttc', 'PingFang.ttc', 'NotoSansSC-Medium.otf', 'NotoSansCJK-Medium.ttc', 'NotoSansCJK-Regular.ttc']


def font(names, size):
    for d in FONT_DIRS:
        for n in names:
            if os.path.exists(os.path.join(d, n)):
                return ImageFont.truetype(os.path.join(d, n), size)
    print('warning: no CJK font found, captions will not render', file=sys.stderr)
    return ImageFont.load_default()


f_title, f_chip, f_cap = font(FONT_BOLD, 48), font(FONT_MED, 28), font(FONT_MED, 24)
PHASES = [('慢走', 0, 3.0), ('甩头＋起跑', 3.0, 4.0), ('跑动', 4.0, 99)]
INK, GRAY, ORANGE = (44, 36, 30), (150, 142, 134), (214, 116, 48)


def compose(T):
    p = params(T)
    fr = R.render(p['neck'], p['head'], p['blocks'], p['hair'])          # premultiplied, body-local
    img = np.empty((H, W, 3), np.float32); img[:] = BG
    # whole horse with body bob / pitch
    small = cv2.resize(fr, (SW, SH), interpolation=cv2.INTER_AREA)
    M = C2V @ R.T3(0, p['bob']) @ R.R3(p['pitch'], *CB) @ F2C @ S_INV
    L = cv2.warpAffine(small, M[:2], (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    img = L[..., :3] + img * (1 - L[..., 3:4])
    # zoom card (body fixed)
    Z = cv2.warpAffine(fr, ZM[:2], (CW, CH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    card = Z[..., :3] + np.ones((CH, CW, 3), np.float32) * (1 - Z[..., 3:4])
    sub = img[CARD[1]:CARD[3], CARD[0]:CARD[2]]
    img[CARD[1]:CARD[3], CARD[0]:CARD[2]] = card * card_mask + sub * (1 - card_mask)
    out = Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))
    d = ImageDraw.Draw(out)
    d.rounded_rectangle(CARD, 22, outline=(224, 218, 209), width=2)
    d.text((56, 30), '脖子＋鬃毛摆动预览', font=f_title, fill=INK)
    x = 58
    for j, (name, a, b) in enumerate(PHASES):
        on = a <= T < b
        tw = d.textlength(name, font=f_chip)
        box = (x, 112, x + tw + 32, 156)
        if on: d.rounded_rectangle(box, 22, fill=ORANGE)
        else: d.rounded_rectangle(box, 22, outline=(214, 207, 198), width=2)
        d.text((x + 16, 114), name, font=f_chip, fill=(255, 255, 255) if on else GRAY)
        x = box[2] + 12
        if j < 2: d.text((x, 114), '→', font=f_chip, fill=(190, 183, 175)); x += 40
    d.text((58, 180), '整体（身体随步态起伏）', font=f_cap, fill=GRAY)
    d.text((CARD[0] + 22, CARD[1] + 16), '局部放大（身体固定）', font=f_cap, fill=GRAY)
    # progress line
    d.rectangle((0, H - 6, W, H), fill=(232, 227, 219)); d.rectangle((0, H - 6, int(W * T / DUR), H), fill=(214, 170, 130))
    return out


def frame_bytes(i):
    return np.asarray(compose(i / FPS)).tobytes()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--still', type=float, nargs='+', metavar='T', help='render stills at these times (s) instead of the video')
    ap.add_argument('--jobs', type=int, default=2, help='worker processes (default 2)')
    ap.add_argument('--out', help='output .mp4 (default <repo>/out/horse-neck-mane-preview.mp4)')
    a = ap.parse_args()
    os.makedirs(OUT_DIR, exist_ok=True)
    if a.still:
        for t in a.still:
            p = os.path.join(OUT_DIR, f'horse-neck-mane-t{t:g}.png')
            compose(t).save(p); print(p)
        return
    out = a.out or os.path.join(OUT_DIR, 'horse-neck-mane-preview.mp4')
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    ff = shutil.which('ffmpeg')
    if ff:
        enc = subprocess.Popen([ff, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                                '-framerate', str(FPS), '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18',
                                '-preset', 'slow', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
        write = enc.stdin.write
    else:
        print('ffmpeg not found: using OpenCV mp4v (lower quality)', file=sys.stderr)
        vw = cv2.VideoWriter(out, cv2.VideoWriter_fourcc(*'mp4v'), FPS, (W, H))
        def write(buf): vw.write(cv2.cvtColor(np.frombuffer(buf, np.uint8).reshape(H, W, 3), cv2.COLOR_RGB2BGR))
    from multiprocessing import Pool
    with Pool(max(1, a.jobs)) as pool:
        for n, buf in enumerate(pool.imap(frame_bytes, range(NF))):
            write(buf)
            if n % 30 == 0: print(f'{n}/{NF}', flush=True)
    if ff:
        enc.stdin.close()
        if enc.wait(): sys.exit('ffmpeg failed')
    else:
        vw.release()
    print(out)


if __name__ == '__main__':
    main()
