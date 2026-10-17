import sys

import numpy as np
from PIL import Image

im = Image.open(sys.argv[1]).convert("RGBA")
a = np.array(im).astype(int)
rgb, alpha = a[:, :, :3], a[:, :, 3]
h, w = alpha.shape


def runs_of(row):
    idx = np.flatnonzero(np.diff(np.concatenate(([0], row.astype(np.int8), [0]))))
    return [(int(idx[i]), int(idx[i + 1])) for i in range(0, len(idx), 2)]


for y in [120, 300, 420, 500, 560, 600, 660, 700, 760, 820, 900, 950, 1000, 1100, 1150, 1200, 1250]:
    solid = alpha[y] > 16
    lum = rgb[y].sum(axis=1)
    dark = (lum < 260) & solid
    orange = (rgb[y][:, 0] - rgb[y][:, 2] > 110) & (rgb[y][:, 0] > 190) & solid
    print(
        f"y={y:4d} alpha={runs_of(solid)}",
        f"dark={runs_of(dark) if dark.any() else []}",
        f"orange={runs_of(orange) if orange.any() else []}",
    )
