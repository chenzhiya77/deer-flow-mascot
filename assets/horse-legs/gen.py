"""Generate the leg + tail pieces, save PNGs + pieces.json, and compose a rest-pose check.

Usage:
  python gen.py        # -> <repo>/out/horse-legs/pieces/*.png, pieces.json, rest_full.png
"""
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parts as P  # noqa: E402
import tailrig as TR  # noqa: E402
from compose import ik2, leg_fk, place  # noqa: E402
from render import finish  # noqa: E402

ASSETS = os.path.dirname(HERE)  # assets/
REPO = os.path.dirname(ASSETS)
OUT = os.path.join(REPO, 'out', 'horse-legs')  # generated pieces stay out of git (out/ is ignored)
BUST_PNG = os.path.join(ASSETS, 'horse-upper', 'horse-bust.png')
PIECES = os.path.join(OUT, 'pieces')

FAR_TINT = (0.86, 0.85, 0.84)
FAR_W = 0.93  # far legs a touch narrower (reference: far front 0.86-0.98 of near)


TAN_GAIN = (0.99, 0.995, 1.05)  # reference tan nudged toward the body piece's tan (legs stay a hair warmer, like the drawing)
LEG_TEX = 0.75  # paper texture strength on legs (reference legs are smoother than the body)


def save(cv, name, seed, tint=None):
    im = finish(cv.rgba(), seed, tex_k=LEG_TEX, tint=tint, gain=TAN_GAIN)
    im.save(os.path.join(PIECES, name + '.png'))
    return {'file': 'pieces/' + name + '.png', 'size': list(im.size), 'pivot': [round(v, 2) for v in cv.pivot]}


def build():
    os.makedirs(PIECES, exist_ok=True)
    man = {}
    man['lf_upper'] = save(P.upper_front(near=True), 'lf_upper', 11)
    man['lf_lower'] = save(P.lower_front(), 'lf_lower', 12)
    man['lf_hoof'] = save(P.hoof_piece('front'), 'lf_hoof', 13)
    man['rf_upper'] = save(P.upper_front(near=False, s=FAR_W), 'rf_upper', 21, FAR_TINT)
    man['rf_lower'] = save(P.lower_front(s=FAR_W), 'rf_lower', 22, FAR_TINT)
    man['rf_hoof'] = save(P.hoof_piece('front', s=FAR_W), 'rf_hoof', 23, FAR_TINT)
    man['lh_upper'] = save(P.upper_hind(), 'lh_upper', 31)
    man['lh_lower'] = save(P.lower_hind(), 'lh_lower', 32)
    man['lh_hoof'] = save(P.hoof_piece('hind'), 'lh_hoof', 33)
    man['rh_upper'] = save(P.upper_hind(s=FAR_W), 'rh_upper', 41, FAR_TINT)
    man['rh_lower'] = save(P.lower_hind(s=FAR_W), 'rh_lower', 42, FAR_TINT)
    man['rh_hoof'] = save(P.hoof_piece('hind', s=FAR_W), 'rh_hoof', 43, FAR_TINT)
    cv = P.tail_piece()
    im = finish(cv.rgba(), 51, tex_k=1.0, dark_tex_k=0.5)
    im.save(os.path.join(PIECES, 'tail.png'))
    man['tail'] = {'file': 'pieces/tail.png', 'size': list(im.size), 'pivot': [round(v, 2) for v in cv.pivot]}
    return man


GROUND = 2630.0
TAIL_AXIS = 9.0  # rest direction of the tail (deg clockwise from straight down): root centre -> tip centre
TAIL_BEND = (120.0, 620.0)  # arc-length span (px from the pivot) over which the droop bends in
SPINE_N = 110.0  # tail spine runs this far behind the pivot axis (mid-tail), so bends squash/stretch both edges evenly
LEGS = {
    # root pivot on the 2048 canvas, rest angles (deg, clockwise from straight down)
    'LF': dict(kind='front', root=(1496.0, 1800.0), near=True),
    'RF': dict(kind='front', root=(1764.0, 1800.0), near=False),
    'LH': dict(kind='hind', root=(349.6, 1714.0), near=True, foot=(182.1, 2504.0)),
    'RH': dict(kind='hind', root=(589.0, 1714.0), near=False, foot=(561.5, 2504.0)),
}


def rest_angles(leg):
    D = P.FRONT if leg['kind'] == 'front' else P.HIND
    if leg['kind'] == 'front':
        return 0.0, 0.0, 0.0
    a_up, a_low = ik2(leg['root'], leg['foot'], D['L1'], D['L2'], +1)
    return a_up, a_low, 0.0


_TAIL_RIG = {}


def tail_rig(man):
    m = man['tail']
    if m['file'] not in _TAIL_RIG:
        rgba = np.array(Image.open(os.path.join(OUT, m['file'])).convert('RGBA'))
        _TAIL_RIG[m['file']] = TR.TailRig(rgba, m['pivot'], TAIL_AXIS, SPINE_N)
    return _TAIL_RIG[m['file']]


def tail_spine(t, length):
    """Tail pose -> spine. t: angle (rigid turn about the pivot), (lift, droop) (ruler bend over TAIL_BEND)
    or 10 per-link deviations (the opening's chain, see tailrig.chain_dev); all degrees from the drawn rest."""
    if isinstance(t, (tuple, list)) and len(t) == TR.NSEG:
        return TR.chain_spine(t, length, TAIL_AXIS, SPINE_N)
    lift, droop = t if isinstance(t, (tuple, list)) else (t, 0.0)
    return TR.ruler_spine(TAIL_AXIS, lift, droop, *TAIL_BEND, SPINE_N)


def unpremultiply(pm):
    a = pm[..., 3:4]
    rgb = np.where(a > 1e-6, pm[..., :3] / np.maximum(a, 1e-6), 0.0)
    return Image.fromarray(np.round(np.clip(np.concatenate([rgb, a], 2), 0, 1) * 255).astype(np.uint8), 'RGBA')


def compose(man, pose=None, bust=True, origin=(-280, -110), size=(2920, 2760), bg=None):
    canvas = Image.new('RGBA', size, (0, 0, 0, 0) if bg is None else bg)
    order = ['TAIL', 'RH', 'RF', 'LH', 'BUST', 'LF']
    bust_im = Image.open(BUST_PNG).convert('RGBA')
    for key in order:
        if key == 'TAIL':
            rig = tail_rig(man)
            layer = rig.render(tail_spine((pose or {}).get('TAIL', 0.0), rig.length), P.TAIL_PIVOT, origin, size)
            canvas.alpha_composite(unpremultiply(layer))
            continue
        if key == 'BUST':
            if bust:
                canvas.alpha_composite(bust_im, (71 - origin[0], -95 - origin[1]))
            continue
        leg = LEGS[key]
        D = P.FRONT if leg['kind'] == 'front' else P.HIND
        a = (pose or {}).get(key) or rest_angles(leg)
        root = leg['root']
        k, f = leg_fk(root, D['L1'], D['L2'], a[0], a[1], a[2])
        pre = key.lower()
        for part, tgt, ang in ((pre + '_upper', root, a[0]), (pre + '_lower', k, a[1]), (pre + '_hoof', f, a[2])):
            m = man[part]
            im = Image.open(os.path.join(OUT, m['file'])).convert('RGBA')
            place(canvas, origin, im, m['pivot'], tgt, ang)
    return canvas


def save_manifest(man):
    with open(os.path.join(OUT, 'pieces.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(man, f, indent=1)


def load_manifest():
    """pieces.json, generating the pieces first if they are missing."""
    p = os.path.join(OUT, 'pieces.json')
    if not os.path.exists(p):
        print('generating pieces -> ' + OUT, flush=True)
        save_manifest(build())
    with open(p, encoding='utf-8') as f:
        return json.load(f)


if __name__ == '__main__':
    man = build()
    save_manifest(man)
    for k, v in LEGS.items():
        print(k, [round(x, 2) for x in rest_angles(v)])
    im = compose(man)
    im.save(os.path.join(OUT, 'rest_full.png'))
    print(OUT)
