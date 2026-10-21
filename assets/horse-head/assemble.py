#!/usr/bin/env python3
"""Rebuild horse-head from pieces/ + manifest.json. Requires Pillow.

Usage: python assemble.py [out.png]
"""
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
spec = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
W, H = spec["canvas"]["w"], spec["canvas"]["h"]

canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
for layer in spec["layers"]:
    im = Image.open(ROOT / layer["file"]).convert("RGBA")
    rect = layer["rect"]
    tw, th = round(rect["w"]), round(rect["h"])
    if im.size != (tw, th):
        im = im.resize((tw, th), Image.LANCZOS)
    canvas.alpha_composite(im, (round(rect["x"]), round(rect["y"])))

out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "horse-head-assembled.png"
canvas.save(out)
print(f"saved {out} ({W}x{H})")
