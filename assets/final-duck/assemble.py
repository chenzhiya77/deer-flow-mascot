#!/usr/bin/env python3
"""Rebuild duck-final from pieces/ + manifest.json. Requires Pillow.

Usage: python assemble.py [out.png] [--eyes STATE]
"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
W, H = manifest["canvas"]["w"], manifest["canvas"]["h"]

parser = argparse.ArgumentParser(description="Rebuild the final duck from pieces + manifest.")
parser.add_argument("out", nargs="?", default=str(ROOT / "duck-assembled.png"))
parser.add_argument("--eyes", default="normal", choices=sorted(manifest.get("eyeStates", {"normal": {}})))
args = parser.parse_args()
eye_state = manifest.get("eyeStates", {}).get(args.eyes, {})

canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
for source in manifest["layers"]:
    layer = dict(source)
    if layer["name"] in eye_state:
        layer["file"] = eye_state[layer["name"]]["file"]
        layer["rect"] = eye_state[layer["name"]]["rect"]
    im = Image.open(ROOT / layer["file"]).convert("RGBA")
    rect = layer["rect"]
    tw, th = round(rect["w"]), round(rect["h"])
    if im.size != (tw, th):
        im = im.resize((tw, th), Image.LANCZOS)
    if "clipPolygon" in layer:
        mask = Image.new("L", (tw, th), 0)
        ImageDraw.Draw(mask).polygon([tuple(p) for p in layer["clipPolygon"]], fill=255)
        im.putalpha(Image.composite(im.getchannel("A"), Image.new("L", (tw, th), 0), mask))
    canvas.alpha_composite(im, (round(rect["x"]), round(rect["y"])))

out = Path(args.out)
canvas.save(out)
print(f"saved {out} ({W}x{H}, eyes={args.eyes})")
