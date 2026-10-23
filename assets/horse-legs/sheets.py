"""Review sheets: pose sheet (body fixed) + parts sheet with pivots.

Usage:
  python sheets.py              # -> <repo>/out/horse-legs/pose_sheet.png, parts_sheet.png
  python sheets.py poses        # only the pose sheet
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen as G  # noqa: E402
import parts as P  # noqa: E402

OUT = G.OUT
FONT_DIRS = ['C:/Windows/Fonts', '/System/Library/Fonts', '/usr/share/fonts/google-noto-cjk',
             '/usr/share/fonts/opentype/noto', '/usr/share/fonts/noto-cjk']
FONT_MED = ['msyh.ttc', 'PingFang.ttc', 'NotoSansSC-Medium.otf', 'NotoSansCJK-Medium.ttc', 'NotoSansCJK-Regular.ttc']
FRAME = ((-760, -110), (3400, 2900))  # pose tiles: room for a lifted tail and folded legs


def cjk_font(size):
    for d in FONT_DIRS:
        for n in FONT_MED:
            if os.path.exists(os.path.join(d, n)):
                return ImageFont.truetype(os.path.join(d, n), size)
    print('warning: no CJK font found, labels will not render', file=sys.stderr)
    return ImageFont.load_default()


def ik_planted(key, dx):
    leg = G.LEGS[key]
    D = P.FRONT if leg['kind'] == 'front' else P.HIND
    if leg['kind'] == 'front':
        foot = (leg['root'][0] + dx, leg['root'][1] + D['L1'] + D['L2'])
        bend = -1
    else:
        foot = (leg['foot'][0] + dx, leg['foot'][1])
        bend = +1
    a_up, a_low = G.ik2(leg['root'], foot, D['L1'], D['L2'], bend)
    return (a_up, a_low, 0.0)


POSES = [
    ('站立（静止）', None),
    ('慢走 A：左前 + 右后抬起', {
        'LF': (-20, 35, 80), 'RF': (12, 12, 0), 'LH': ik_planted('LH', 80), 'RH': (8, 40, 85), 'TAIL': (6, 3)}),
    ('慢走 B：右前 + 左后抬起', {
        'LF': (12, 12, 0), 'RF': (-20, 35, 80), 'LH': (10, 40, 85), 'RH': ik_planted('RH', 70), 'TAIL': (3, 2)}),
    ('跑动：腾空伸展，尾巴根 +50° / 梢 −22°', {
        'LF': (-45, -60, -50), 'RF': (-30, -40, -20), 'LH': (50, 70, 95), 'RH': (40, 55, 80), 'TAIL': (50, 22)}),
    ('跑动：收腿，尾巴根 +28° / 梢 −10°', {
        'LF': (20, 105, 150), 'RF': (5, 80, 120), 'LH': (-20, -15, 20), 'RH': (-5, 5, 40), 'TAIL': (28, 10)}),
    ('关节极限检查，尾巴根 +68° / 梢 −30°', {
        'LF': (-30, 90, 165), 'RF': (-50, -50, -40), 'LH': (-35, 60, 110), 'RH': (60, 60, 100), 'TAIL': (68, 30)}),
]


def pose_sheet(man, scale=4, cols=3):
    font = cjk_font(34)
    tiles = []
    for title, pose in POSES:
        im = G.compose(man, pose, origin=FRAME[0], size=FRAME[1])
        bg = Image.new('RGBA', im.size, (255, 255, 255, 255))
        d = ImageDraw.Draw(bg)
        gy = G.GROUND - FRAME[0][1]
        d.line([(0, gy), (im.size[0], gy)], fill=(200, 200, 200, 255), width=6)
        bg.alpha_composite(im)
        t = bg.convert('RGB').resize((im.size[0] // scale, im.size[1] // scale), Image.LANCZOS)
        tile = Image.new('RGB', (t.size[0], t.size[1] + 50), (255, 255, 255))
        tile.paste(t, (0, 50))
        ImageDraw.Draw(tile).text((14, 6), title, font=font, fill=(40, 40, 40))
        tiles.append(tile)
    w, h = tiles[0].size
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * w + (cols - 1) * 10, rows * h + (rows - 1) * 10), (225, 225, 225))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * (w + 10), (i // cols) * (h + 10)))
    return sheet


def parts_sheet(man, scale=2):
    font = cjk_font(26)
    order = [['lf_upper', 'lf_lower', 'lf_hoof', 'rf_upper', 'rf_lower', 'rf_hoof'],
             ['lh_upper', 'lh_lower', 'lh_hoof', 'rh_upper', 'rh_lower', 'rh_hoof', 'tail']]
    names = {'lf': '左前（近）', 'rf': '右前（远）', 'lh': '左后（近）', 'rh': '右后（远）'}
    seg = {'upper': '上段', 'lower': '下段+护箍', 'hoof': '蹄'}
    rows = []
    for row in order:
        cells = []
        for k in row:
            m = man[k]
            im = Image.open(os.path.join(OUT, m['file'])).convert('RGBA')
            pad = 24
            c = Image.new('RGBA', (im.size[0] + 2 * pad, im.size[1] + 2 * pad), (246, 243, 238, 255))
            d = ImageDraw.Draw(c)
            for yy in range(0, c.size[1], 40):  # light checker to show transparency
                for xx in range(0, c.size[0], 40):
                    if (xx // 40 + yy // 40) % 2:
                        d.rectangle([xx, yy, xx + 39, yy + 39], fill=(234, 230, 224, 255))
            c.alpha_composite(im, (pad, pad))
            px, py = m['pivot'][0] + pad, m['pivot'][1] + pad
            d = ImageDraw.Draw(c)
            d.ellipse([px - 14, py - 14, px + 14, py + 14], outline=(230, 30, 60, 255), width=5)
            d.line([(px - 26, py), (px + 26, py)], fill=(230, 30, 60, 255), width=4)
            d.line([(px, py - 26), (px, py + 26)], fill=(230, 30, 60, 255), width=4)
            D = P.FRONT if k[1] == 'f' else P.HIND
            child = {'upper': D['L1'], 'lower': D['L2']}.get(k[3:]) if k != 'tail' else None
            if child:  # where the next piece's pivot sits (knee/hock, fetlock)
                cy = py + child
                d.ellipse([px - 16, cy - 16, px + 16, cy + 16], outline=(30, 110, 230, 255), width=5)
            c = c.convert('RGB').resize((c.size[0] // scale, c.size[1] // scale), Image.LANCZOS)
            lines = ['尾巴'] if k == 'tail' else [names[k[:2]], seg[k[3:]]]
            tw = max(int(ImageDraw.Draw(c).textlength(t, font=font)) for t in lines) + 8
            top = 34 * len(lines) + 6
            cell = Image.new('RGB', (max(c.size[0], tw), c.size[1] + top), (255, 255, 255))
            cell.paste(c, (0, top))
            for li, t in enumerate(lines):
                ImageDraw.Draw(cell).text((4, 2 + 34 * li), t, font=font, fill=(40, 40, 40))
            cells.append(cell)
        H = max(c.size[1] for c in cells)
        W = sum(c.size[0] for c in cells) + 16 * (len(cells) - 1)
        r = Image.new('RGB', (W, H), (255, 255, 255))
        x = 0
        for c in cells:
            r.paste(c, (x, 0))
            x += c.size[0] + 16
        rows.append(r)
    W = max(r.size[0] for r in rows) + 40
    H = sum(r.size[1] for r in rows) + 30 * (len(rows) - 1) + 100
    sheet = Image.new('RGB', (W, H), (255, 255, 255))
    y = 20
    for r in rows:
        sheet.paste(r, (20, y))
        y += r.size[1] + 30
    ImageDraw.Draw(sheet).text((20, H - 50), '红十字 = 本件转轴；蓝圈 = 下一件的转轴（膝 / 飞节、球节）；1:2 缩小', font=font, fill=(120, 30, 40))
    return sheet


if __name__ == '__main__':
    man = G.load_manifest()
    what = sys.argv[1:] or ['poses', 'parts']
    if 'poses' in what:
        pose_sheet(man).save(os.path.join(OUT, 'pose_sheet.png'))
        print('pose_sheet')
    if 'parts' in what:
        parts_sheet(man).save(os.path.join(OUT, 'parts_sheet.png'))
        print('parts_sheet')
