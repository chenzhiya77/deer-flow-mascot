"""Assemble body + new neck (neck with trimmed mane) + horse head.

The pack keeps its own source pieces: pieces/body.png and pieces/neck.png are
1:1 copies of the Desktop art; the saddle and head come from ../horse-saddle/
and ../horse-head/. The Desktop reference art is optional verification only:
when `图片-调色样张.png`, `ma-bozi.png` or `ma-cankao.png` are missing, the
corresponding checks are skipped and the finals still rebuild.

The new neck is a redraw, so it is registered to the reference's neck cutout
by silhouette: scale 2.217, offset (1251, 96) on the 2048 canvas, bottom-edge
residual 1.25px, throat-edge residual 2.06px.

The new neck is drawn directly over the body; its trimmed rear-bottom is
covered by the body. The old reference neck backing (previously masked to
canvas y >= 1000) and the sampled seam fill were removed on 2026-10-23, so
the pack contains no old-neck piece.

The saddle is the complete 339x240 piece (no baked notch), drawn ABOVE the neck
and never trimmed. The reference fit is a 1.0414x enlargement anchored at its
brown bottom-left, plus a +8px forward nudge so the front edge meets the mane's
inner line at its end. That lifts the left curl off the body and extends the
right side over the neck's end corner; the alignment with the mane's line is
the only intended difference from ma-cankao. No sampled pixels are used at the
connection, and the standalone saddle asset stays complete for animation.

Verification previews and checks are written to the system temp folder
(horse-upper-checks), outside the pack.

Usage: python assemble.py
"""

import json
import os
import tempfile
from collections import deque

import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
DESKTOP = r"C:\Users\h7242\Desktop\道具素材"
HORSE_DIR = os.path.join(DESKTOP, "小黄鸭的马")

REF_SIZE = 2048
FRAME_ORIGIN = (-140, -260)  # 2048-frame -> raw canvas
FRAME_MAX = (2660, 1960)  # head reaches x~2611, body bottom y~1924

BODY_FILE = os.path.join("pieces", "body.png")
BODY_XY = (71, 1074)  # body.png crop origin on the 2048 canvas

NECK_SRC = os.path.join(ROOT, "pieces", "neck.png")  # 1:1 copy of Desktop\道具素材\1-matou_副本.png
NECK_SCALE = 2.217
NECK_XY = (1251, 96)

# silhouette-fit reference only; never composited
FIT_REF_SRC = os.path.join(HORSE_DIR, "ma-bozi.png")
FIT_REF_XY = (965, 118)  # old-neck cutout offset, used only by profile_errors

CHECK_DIR = os.path.join(tempfile.gettempdir(), "horse-upper-checks")

SADDLE_SRC = os.path.join(ROOT, "..", "horse-saddle", "saddle.png")
# Complete 339x240 saddle (no baked notch). The first reference fit (2.1281 at
# 547.2,951) read ~4% small: the curl sat on the body and the right side stopped
# short of the neck corner. Refit with a 1.0414x enlargement anchored at the
# saddle's brown bottom-left, then nudged +8px forward so the front edge meets
# the mane's inner line at its end (both x=1299 on the 2048 canvas).
SADDLE_SCALE = 2.2162
SADDLE_XY = (554.2, 930.9)

HEAD_SRC = os.path.join(ROOT, "..", "horse-head", "horse-head.png")
HEAD_SCALE = 2.2497
HEAD_XY = (1890.89, -93.36)  # ma-cankao reference fit (no 6px band drop)

REF_SRC = os.path.join(HORSE_DIR, "图片-调色样张.png")

SOLID = 250


def load(path):
    return Image.open(path).convert("RGBA")


def scaled(piece, scale):
    return piece.resize((round(piece.width * scale), round(piece.height * scale)), Image.LANCZOS)


def to_canvas(xy):
    return (round(xy[0] - FRAME_ORIGIN[0]), round(xy[1] - FRAME_ORIGIN[1]))


def dilate(mask, radius):
    im = Image.fromarray((mask * 255).astype(np.uint8))
    return np.array(im.filter(ImageFilter.MaxFilter(2 * radius + 1))) > 0


def fill_region_from_source(canvas, region, source_mask):
    """Fill a thin gap with the nearest solid colours from source_mask."""
    arr = np.array(canvas)
    ys, xs = np.where(region)
    if not len(ys):
        return canvas, 0, None
    y0, y1 = max(0, int(ys.min()) - 8), min(arr.shape[0], int(ys.max()) + 9)
    x0, x1 = max(0, int(xs.min()) - 8), min(arr.shape[1], int(xs.max()) + 9)
    patch = arr[y0:y1, x0:x1]
    fill = region[y0:y1, x0:x1]
    known = source_mask[y0:y1, x0:x1] & (patch[..., 3] >= SOLID)
    colors = patch[..., :3].copy()
    seen = known.copy()
    queue = deque(tuple(pos) for pos in np.argwhere(known))
    while queue:
        yy, xx = queue.popleft()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                ny, nx = yy + dy, xx + dx
                if (
                    0 <= ny < patch.shape[0]
                    and 0 <= nx < patch.shape[1]
                    and not seen[ny, nx]
                ):
                    seen[ny, nx] = True
                    colors[ny, nx] = colors[yy, xx]
                    queue.append((ny, nx))
    patch[fill, :3] = colors[fill]
    patch[fill, 3] = 255
    arr[y0:y1, x0:x1] = patch
    bbox = [
        int(xs.min()) + FRAME_ORIGIN[0],
        int(ys.min()) + FRAME_ORIGIN[1],
        int(xs.max()) + FRAME_ORIGIN[0],
        int(ys.max()) + FRAME_ORIGIN[1],
    ]
    return Image.fromarray(arr), int(len(ys)), bbox


def alpha_mask(canvas):
    return np.array(canvas)[..., 3]


def frame_crop(canvas, bbox):
    x0, y0, x1, y1 = bbox
    return canvas.crop(
        (
            x0 - FRAME_ORIGIN[0],
            y0 - FRAME_ORIGIN[1],
            x1 - FRAME_ORIGIN[0],
            y1 - FRAME_ORIGIN[1],
        )
    )


def save_previews(image, stem):
    os.makedirs(CHECK_DIR, exist_ok=True)
    checker = Image.new("RGBA", image.size, (255, 255, 255, 255))
    px = np.array(checker)
    yy, xx = np.mgrid[0 : image.size[1], 0 : image.size[0]]
    tile = ((xx // 24) + (yy // 24)) % 2
    px[..., :3] = np.where(tile[..., None] == 1, 222, 255)
    checker = Image.fromarray(px)
    checker.alpha_composite(image)
    checker.convert("RGB").save(os.path.join(CHECK_DIR, stem + "-preview.png"))
    white = Image.new("RGBA", image.size, (255, 255, 255, 255))
    white.alpha_composite(image)
    white.convert("RGB").save(os.path.join(CHECK_DIR, stem + "-white.png"))


def save_check(canvas, name, box, zoom=2):
    os.makedirs(CHECK_DIR, exist_ok=True)
    x0, y0, x1, y1 = box
    crop = canvas.crop(
        (
            x0 - FRAME_ORIGIN[0],
            y0 - FRAME_ORIGIN[1],
            x1 - FRAME_ORIGIN[0],
            y1 - FRAME_ORIGIN[1],
        )
    )
    crop.resize((crop.width * zoom, crop.height * zoom), Image.NEAREST).save(
        os.path.join(CHECK_DIR, name)
    )


def profile_errors(neck_mask, old_mask):
    """Bottom- and throat-edge residuals of the placed neck vs the reference cutout."""
    s = NECK_SCALE
    X0, Y0 = NECK_XY
    old_x, old_y = FIT_REF_XY
    bottom, throat = [], []
    for x in range(1340, 1911, 2):
        ys = np.where(old_mask[:, x - old_x])[0]
        nx = round(x - X0)
        if not len(ys) or not (0 <= nx < neck_mask.shape[1]):
            continue
        col = np.where(neck_mask[:, nx])[0]
        if len(col):
            bottom.append(abs(Y0 + col.max() - (ys.max() + old_y)))
    for y in range(300, 1301, 2):
        xs = np.where(old_mask[y - old_y])[0]
        ny = round(y - Y0)
        if not len(xs) or not (0 <= ny < neck_mask.shape[0]):
            continue
        row = np.where(neck_mask[ny])[0]
        if len(row):
            throat.append(abs(X0 + row.max() - (xs.max() + old_x)))
    return {
        "bottom": {
            "samples": len(bottom),
            "meanPx": round(float(np.mean(bottom)), 2),
            "maxPx": round(float(np.max(bottom)), 2),
        },
        "throat": {
            "samples": len(throat),
            "meanPx": round(float(np.mean(throat)), 2),
            "maxPx": round(float(np.max(throat)), 2),
        },
    }


def main():
    body = load(os.path.join(ROOT, BODY_FILE))
    neck = scaled(load(NECK_SRC), NECK_SCALE)
    fit_ref = load(FIT_REF_SRC) if os.path.exists(FIT_REF_SRC) else None
    saddle = scaled(load(SADDLE_SRC), SADDLE_SCALE)
    head = scaled(load(HEAD_SRC), HEAD_SCALE)
    ref = np.array(load(REF_SRC).convert("RGB")) if os.path.exists(REF_SRC) else None

    raw_w = FRAME_MAX[0] - FRAME_ORIGIN[0]
    raw_h = FRAME_MAX[1] - FRAME_ORIGIN[1]
    canvas = Image.new("RGBA", (raw_w, raw_h), (0, 0, 0, 0))
    canvas.alpha_composite(body, to_canvas(BODY_XY))

    # the new neck is drawn directly over the body; no old-neck backing
    canvas.alpha_composite(neck, to_canvas(NECK_XY))

    arr = np.array(canvas)
    solid = arr[..., 3] >= SOLID
    body_mask = np.zeros_like(solid)
    body_arr = np.array(body)
    body_mask[
        BODY_XY[1] - FRAME_ORIGIN[1] : BODY_XY[1] - FRAME_ORIGIN[1] + body.height,
        BODY_XY[0] - FRAME_ORIGIN[0] : BODY_XY[0] - FRAME_ORIGIN[0] + body.width,
    ] = body_arr[..., 3] >= SOLID
    saddle_mask = np.zeros_like(solid)
    sx0, sy0 = to_canvas(SADDLE_XY)
    saddle_mask[sy0 : sy0 + saddle.height, sx0 : sx0 + saddle.width] = (
        np.array(saddle)[..., 3] > 0
    )
    neck_mask = np.array(neck)[..., 3] >= SOLID
    old_mask = np.array(fit_ref)[..., 3] >= SOLID if fit_ref is not None else None
    neck_placed = np.zeros_like(solid)
    neck_placed[
        NECK_XY[1] - FRAME_ORIGIN[1] : NECK_XY[1] - FRAME_ORIGIN[1] + neck.height,
        NECK_XY[0] - FRAME_ORIGIN[0] : NECK_XY[0] - FRAME_ORIGIN[0] + neck.width,
    ] = neck_mask
    neck_alpha_placed = np.zeros_like(solid)
    neck_alpha_placed[
        NECK_XY[1] - FRAME_ORIGIN[1] : NECK_XY[1] - FRAME_ORIGIN[1] + neck.height,
        NECK_XY[0] - FRAME_ORIGIN[0] : NECK_XY[0] - FRAME_ORIGIN[0] + neck.width,
    ] = np.array(neck)[..., 3] > 0

    # the trimmed neck edge leaves a 1-2px gap at the withers; close it with
    # the nearest body colours (no old-neck pixels)
    gap = (
        (~solid)
        & dilate(body_mask, 4)
        & dilate(neck_alpha_placed, 4)
        & ~dilate(saddle_mask, 2)
    )
    canvas, gap_pixels, gap_bbox = fill_region_from_source(canvas, gap, body_mask)

    # a thin light strip remains between the saddle's front edge and the neck's
    # soft inner edge; back only that strip, below the saddle's top corner, with
    # the new neck's own edge colours so no tab sticks out above the saddle
    arr = np.array(canvas)
    solid = arr[..., 3] >= SOLID
    yy, xx = np.indices(solid.shape)
    edge = (
        (arr[..., 3] > 0)
        & (~solid)
        & dilate(saddle_mask, 8)
        & dilate(neck_placed, 16)
        & (xx >= sx0 + saddle.width - 10)
        & (yy >= 958 - FRAME_ORIGIN[1])
        & (yy <= 1120 - FRAME_ORIGIN[1])
    )
    canvas, edge_pixels, edge_bbox = fill_region_from_source(canvas, edge, neck_placed)
    seam = {
        "method": "neck-body gap filled from the nearest body colours; the thin saddle-edge strip is backed with the new neck's own edge colours, below the saddle top (no old-neck pixels)",
        "bodyGap": {"pixels": gap_pixels, "bbox": gap_bbox},
        "saddleEdge": {"pixels": edge_pixels, "bbox": edge_bbox},
    }

    # the complete saddle stays unmodified and sits above the neck; its right
    # panel intentionally covers the neck's end corner
    canvas.alpha_composite(saddle, to_canvas(SADDLE_XY))

    # verify after the saddle is composited
    arr = np.array(canvas)
    solid = arr[..., 3] >= SOLID
    saddle_neck_overlap = int((saddle_mask & neck_alpha_placed).sum())
    body_erode = ~dilate(~body_mask, 1)
    neck_erode = ~dilate(~neck_placed, 1)
    holes = int((~solid & (body_erode | neck_erode)).sum())

    union = arr[..., 3] > 0
    ys, xs = np.where(union)
    neck_bbox = [
        int(xs.min()) + FRAME_ORIGIN[0],
        int(ys.min()) + FRAME_ORIGIN[1],
        int(xs.max()) + FRAME_ORIGIN[0],
        int(ys.max()) + FRAME_ORIGIN[1],
    ]
    crop = [neck_bbox[0] - 2, neck_bbox[1] - 2, neck_bbox[2] + 3, neck_bbox[3] + 3]
    horse_upper = frame_crop(canvas, crop)
    horse_upper.save(os.path.join(ROOT, "horse-upper.png"))
    save_previews(horse_upper, "horse-upper")

    canvas.alpha_composite(head, to_canvas(HEAD_XY))
    arr2 = np.array(canvas)
    solid2 = arr2[..., 3] >= SOLID
    ys2, xs2 = np.where(arr2[..., 3] > 0)
    bust_bbox = [
        int(xs2.min()) + FRAME_ORIGIN[0],
        int(ys2.min()) + FRAME_ORIGIN[1],
        int(xs2.max()) + FRAME_ORIGIN[0],
        int(ys2.max()) + FRAME_ORIGIN[1],
    ]
    bust_crop = [bust_bbox[0] - 2, bust_bbox[1] - 2, bust_bbox[2] + 3, bust_bbox[3] + 3]
    horse_bust = frame_crop(canvas, bust_crop)
    horse_bust.save(os.path.join(ROOT, "horse-bust.png"))
    save_previews(horse_bust, "horse-bust")

    head_mask = np.zeros_like(solid2)
    head_mask[
        round(HEAD_XY[1]) - FRAME_ORIGIN[1] : round(HEAD_XY[1]) - FRAME_ORIGIN[1] + head.height,
        round(HEAD_XY[0]) - FRAME_ORIGIN[0] : round(HEAD_XY[0]) - FRAME_ORIGIN[0] + head.width,
    ] = np.array(head)[..., 3] >= SOLID
    head_neck_overlap = int((head_mask & neck_placed).sum())
    neck_body_gap = int((~solid & dilate(body_mask, 4) & dilate(neck_placed, 4)).sum())
    head_neck_gap = int((~solid2 & dilate(head_mask, 4) & dilate(neck_placed, 4)).sum())

    save_check(canvas, "neck-withers-check.png", (1130, 900, 1520, 1250))
    save_check(canvas, "saddle-check.png", (520, 900, 1330, 1520))
    save_check(canvas, "saddle-connection-check.png", (1150, 930, 1380, 1180), zoom=4)
    save_check(canvas, "head-junction-check.png", (1740, -60, 2160, 460))
    save_check(canvas, "neck-throat-check.png", (1800, 650, 2250, 1450))

    # ma-cankao overlay of the final bust (reference frame: ma = 2048*0.4445 + (429.5,86.5))
    cankao_path = os.path.join(HORSE_DIR, "ma-cankao.png")
    if os.path.exists(cankao_path):
        cankao = load(cankao_path)
        overlay = Image.new("RGBA", cankao.size, (255, 255, 255, 255))
        overlay.alpha_composite(cankao)
        small = horse_bust.resize(
            (round(horse_bust.width * 0.4445), round(horse_bust.height * 0.4445)), Image.LANCZOS
        )
        layer = Image.new("RGBA", cankao.size, (0, 0, 0, 0))
        layer.alpha_composite(
            small,
            (
                round(bust_crop[0] * 0.4445 + 429.5),
                round(bust_crop[1] * 0.4445 + 86.5),
            ),
        )
        layer_arr = np.array(layer)
        layer_arr[..., 3] = (layer_arr[..., 3].astype(np.float32) * 0.55).astype(np.uint8)
        overlay.alpha_composite(Image.fromarray(layer_arr))
        overlay.convert("RGB").save(os.path.join(CHECK_DIR, "cankao-overlay-check.png"))

    # colour check at the junction (body sample needs the desktop reference)
    body_tan = ref[1150:1250, 1200:1300].reshape(-1, 3).mean(axis=0) if ref is not None else None
    neck_arr = np.array(neck)
    neck_patch = neck_arr[554:776, 399:577]
    neck_tan = neck_patch[neck_patch[..., 3] > 250][:, :3].mean(axis=0)

    placements = {
        "name": "horse-upper",
        "snapshotDate": "2026-10-23",
        "reference": "图片-调色样张.png",
        "referenceCanvas": {"w": REF_SIZE, "h": REF_SIZE},
        "frame": "placements are on the 2048x2048 reference canvas",
        "placements": [
            {"name": "body", "file": "pieces/body.png", "x": BODY_XY[0], "y": BODY_XY[1], "scale": 1},
            {
                "name": "saddle",
                "source": "assets/horse-saddle/saddle.png",
                "x": round(SADDLE_XY[0], 1),
                "y": round(SADDLE_XY[1], 1),
                "scale": SADDLE_SCALE,
                "note": "complete 339x240 no-white-edge saddle (ma-maan-wanzheng.png), no baked notch and no trim. Reference fit enlarged 1.0414x from the first 2.1281 fit, anchored at the saddle's brown bottom-left, then nudged +8px forward (x 546.2 -> 554.2): the front edge meets the mane's inner line at its end (both x=1299 on the 2048 canvas). The horn highlight moves with it to ma (697.9,534.9), 7.2px right of ma-cankao's (690.7,534.7). The saddle is drawn ABOVE the neck; its complete right panel intentionally covers the neck's end corner, the only intended difference from ma-cankao. Layer: above the neck, below the head.",
            },
            {
                "name": "neck",
                "source": "pieces/neck.png",
                "x": NECK_XY[0],
                "y": NECK_XY[1],
                "scale": NECK_SCALE,
                "note": "new neck with trimmed mane glued on; 1:1 copy of Desktop\\道具素材\\1-matou_副本.png; drawn larger than ma-cankao (not a pixel copy), registered to the reference neck cutout by silhouette. Drawn directly over the body: the old reference backing and sampled seam fill were removed on 2026-10-23, so no old-neck piece remains.",
            },
            {
                "name": "head",
                "source": "assets/horse-head/horse-head.png",
                "x": HEAD_XY[0],
                "y": HEAD_XY[1],
                "scale": HEAD_SCALE,
                "note": "ma-cankao fit (eye and nostril). The 6px drop from the banded assembly is NOT applied: it compensated for the old separate mane band, which this neck piece replaces.",
            },
        ],
        "fit": profile_errors(neck_mask, old_mask) if old_mask is not None else {"skipped": "ma-bozi.png not available"},
        "seam": seam,
        "saddleLayer": {
            "order": "above neck, below head",
            "complete": True,
            "trimmed": False,
            "neckOverlapPx": saddle_neck_overlap,
            "note": "complete saddle covers the neck's end corner; no RGB sampling at the connection",
        },
        "verification": {
            "interiorHolesAfterNeck": holes,
            "neckBodyGapPx": neck_body_gap,
            "headNeckGapPx": head_neck_gap,
            "headNeckOverlapSolidPx": head_neck_overlap,
            "tanBody": [round(float(v), 1) for v in body_tan] if body_tan is not None else None,
            "tanNewNeck": [round(float(v), 1) for v in neck_tan],
        },
        "images": {
            "upper": {
                "file": "horse-upper.png",
                "canvas": [horse_upper.width, horse_upper.height],
                "cropOriginOn2048Canvas": crop[:2],
                "note": "body + saddle + new neck; 1:1 with the 2048 canvas, cropped to the union bbox plus 2px",
            },
            "bust": {
                "file": "horse-bust.png",
                "canvas": [horse_bust.width, horse_bust.height],
                "cropOriginOn2048Canvas": bust_crop[:2],
                "note": "body + saddle + new neck + head; same frame as upper, plus the head",
            },
        },
    }
    with open(os.path.join(ROOT, "placements.json"), "w", encoding="utf-8") as f:
        json.dump(placements, f, ensure_ascii=False, indent=2)
    print(json.dumps(placements["fit"], ensure_ascii=False))
    print(json.dumps(placements["verification"], ensure_ascii=False))
    print("upper", horse_upper.size, "crop", crop, "bust", horse_bust.size, "crop", bust_crop)
    print("seam", seam)


if __name__ == "__main__":
    main()
