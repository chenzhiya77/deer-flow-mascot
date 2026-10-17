import sys

import numpy as np
from PIL import Image
from scipy import ndimage

im = Image.open(sys.argv[1]).convert("RGBA")
a = np.array(im).astype(int)
rgb, alpha = a[:, :, :3], a[:, :, 3]
solid = alpha > 16
lum = rgb.sum(axis=2)
dark = lum < 330
free = solid & ~dark
free = ndimage.binary_closing(free, np.ones((3, 3)))
labels, n = ndimage.label(free)
print("components:", n)
sizes = ndimage.sum(free, labels, range(1, n + 1))
order = np.argsort(-sizes)
for i in order[:25]:
    lab = i + 1
    if sizes[i] < 400:
        break
    ys, xs = np.where(labels == lab)
    print(
        f"#{lab:3d} size={int(sizes[i]):7d} bbox=({int(xs.min())},{int(ys.min())},{int(xs.max())},{int(ys.max())})"
    )
