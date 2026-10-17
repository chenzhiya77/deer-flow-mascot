import sys

import numpy as np
from PIL import Image


def metrics(name, img):
    q = img.quantize(colors=6, method=Image.MEDIANCUT).convert("RGB")
    a = np.array(q)
    h, w, _ = a.shape
    runs = []
    for row in a:
        idx = np.flatnonzero((row[1:] != row[:-1]).any(axis=1)) + 1
        segs = np.diff(np.concatenate(([0], idx, [w])))
        runs.extend(segs.tolist())
    runs = np.array(runs)
    right = np.zeros((h, w), bool)
    right[:, :-1] = (a[:, 1:] != a[:, :-1]).any(axis=2)
    down = np.zeros((h, w), bool)
    down[:-1, :] = (a[1:, :] != a[:-1, :]).any(axis=2)
    edge = float((right | down).mean())
    corner = float((right & down).mean())
    print(
        f"{name}\tmean_run={runs.mean():.2f}\truns<=2={np.mean(runs <= 2):.3f}"
        f"\tedge_px={edge:.3f}\tcorner/edge={corner / max(edge, 1e-9):.3f}",
        flush=True,
    )


base = sys.argv[1]
clawd = Image.open(f"{base}/f912949f-a28a-4e77-b8fd-4c0fbff13167.png").convert("RGB")
grid = Image.open(f"{base}/404dda4f-100d-4c78-8e5f-b56e621124b5.png").convert("RGB")
gen = Image.open(f"{base}/37a6bd7c-9ee1-44fe-9ff8-80fb2e581094.png").convert("RGB")

cw, ch = clawd.size
metrics("clawd_single      ", clawd)
metrics("clawd_body_crop   ", clawd.crop((cw // 2 - 55, ch // 2 - 35, cw // 2 + 55, ch // 2 + 35)))
gw, gh = grid.size
metrics("clawd_tile_headph ", grid.crop((0, 0, gw // 4, gh // 6)))
metrics("clawd_tile_plain  ", grid.crop((3 * gw // 4, gh // 6, gw, 2 * gh // 6)))
metrics("gen_duck_full     ", gen)
w2, h2 = gen.size
metrics("gen_duck_center   ", gen.crop((w2 // 2 - 100, h2 // 2 - 100, w2 // 2 + 100, h2 // 2 + 100)))
