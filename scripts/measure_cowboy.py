import sys

import numpy as np
from PIL import Image

src = sys.argv[1]
im = Image.open(src).convert("RGBA")
a = np.array(im).astype(int)
rgb, alpha = a[:, :, :3], a[:, :, 3]
h, w = alpha.shape
solid = alpha > 16


def bbox(mask):
    ys, xs = np.where(mask)
    if not len(xs):
        return None
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def near(color, tol):
    return (np.sqrt(((rgb - np.array(color)) ** 2).sum(axis=2)) < tol) & solid


ys, xs = np.where(solid)
print("silhouette", (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())), "of", (w, h))

hat = near((220, 199, 166), 55) | near((107, 85, 64), 45)
hat_top = np.zeros_like(hat)
hat_top[: int(h * 0.45)] = True
print("hat   ", bbox(hat & hat_top))

bolt = near((245, 197, 66), 40)
print("bolt  ", bbox(bolt))

eye = (rgb.sum(axis=2) < 220) & solid
mid = np.zeros_like(eye)
mid[int(h * 0.33) : int(h * 0.58)] = True
print("eyes  ", bbox(eye & mid))

beak_o = near((242, 168, 99), 55) | near((224, 139, 69), 55)
beak_zone = np.zeros_like(beak_o)
beak_zone[int(h * 0.44) : int(h * 0.62)] = True
print("beak  ", bbox(beak_o & beak_zone))

belt = near((74, 56, 38), 50)
belt_zone = np.zeros_like(belt)
belt_zone[int(h * 0.58) : int(h * 0.75)] = True
print("belt  ", bbox(belt & belt_zone))

hand = near((243, 210, 142), 45)
hz = np.zeros_like(hand)
hz[int(h * 0.55) : int(h * 0.80)] = True
hand = hand & hz
cols = hand.any(axis=0)
runs = np.flatnonzero(np.diff(np.concatenate(([0], cols.view(np.int8), [0]))))
print("hand col runs", [(int(runs[i]), int(runs[i + 1])) for i in range(0, len(runs), 2)])

boot = near((240, 164, 94), 60) | near((232, 148, 75), 60)
bz = np.zeros_like(boot)
bz[int(h * 0.68) :] = True
boot = boot & bz
cols = boot.any(axis=0)
runs = np.flatnonzero(np.diff(np.concatenate(([0], cols.view(np.int8), [0]))))
print("boot col runs", [(int(runs[i]), int(runs[i + 1])) for i in range(0, len(runs), 2)])
print("boot bbox", bbox(boot))
rows = boot.any(axis=1)
rr = np.flatnonzero(rows)
print("boot rows", int(rr.min()), int(rr.max()))
