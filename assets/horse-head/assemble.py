#!/usr/bin/env python3
"""Rebuild horse-head from pieces/ + manifest.json. Requires Pillow.

Usage: python assemble.py [out.png] [--eye STATE]
"""
import argparse
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
spec = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
W, H = spec["canvas"]["w"], spec["canvas"]["h"]
eye_states = spec.get("eyeStates", {})

parser = argparse.ArgumentParser(description="Rebuild the horse head from pieces + manifest.")
parser.add_argument("out", nargs="?", default=str(ROOT / "horse-head-assembled.png"))
parser.add_argument("--eye", default=spec.get("state", {}).get("eye", "normal"), choices=sorted(eye_states))
args = parser.parse_args()
eye_state = eye_states.get(args.eye, {})

canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
for source in spec["layers"]:
    layer = dict(source)
    if layer["name"] in eye_state:
        layer["file"] = eye_state[layer["name"]]["file"]
        layer["rect"] = eye_state[layer["name"]]["rect"]
    im = Image.open(ROOT / layer["file"]).convert("RGBA")
    rect = layer["rect"]
    tw, th = round(rect["w"]), round(rect["h"])
    if im.size != (tw, th):
        im = im.resize((tw, th), Image.LANCZOS)
    canvas.alpha_composite(im, (round(rect["x"]), round(rect["y"])))

out = Path(args.out)
canvas.save(out)
print(f"saved {out} ({W}x{H}, eye={args.eye})")
