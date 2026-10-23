"""Leg + tail piece geometry (canvas px; each piece in its own frame, pivot at 0,0, +y down)."""
import math

from geom import arc, chamfer_rect, lerp
from render import OL, Canvas, bevel_block, fill_poly, outline, path_poly, c255

TAN = dict(
    face=(238, 167, 97),
    hl_col=(253, 222, 182),
    col=dict(up=(252, 216, 166), left=(214, 146, 74), right=(190, 130, 68), down=(178, 117, 55)),
)
SEG_STYLE = dict(TAN, bw=dict(up=20, left=17, right=33, down=13), hl=dict(up=0, left=13, right=0, down=0), rim=dict(up=0, left=0, right=5, down=5), rim_k=0.86)
BAND_STYLE = dict(
    face=(238, 166, 93),
    hl_col=(244, 192, 132),
    col=dict(up=(249, 201, 142), left=(209, 142, 68), right=(187, 128, 60), down=(178, 116, 54)),
    bw=dict(up=11, left=36, right=30, down=13),
    hl=dict(up=0, left=5, right=0, down=0),
    rim=dict(up=0, left=0, right=4, down=4),
    rim_k=0.86,
)
HOOF_STYLE = dict(
    face=(48, 37, 32),
    hl_col=(74, 58, 51),
    col=dict(up=(52, 41, 35), left=(48, 37, 32), right=(32, 27, 23), down=(34, 29, 26)),
    bw=dict(up=3, left=18, right=40, down=9),
    hl=dict(up=0, left=13, right=0, down=0),
    rim=dict(up=0, left=0, right=3, down=3),
    rim_k=0.8,
)
UNDER_BAND_SHADOW = (150, 96, 44)
HOCK_HL = (250, 234, 212)


def taper_seg(hw_top, hw_bot, y_top, y_bot, top='round', bot='round', chamfer=16, top_center=None, bot_center=None, n=28, bot_k=1.0, joint=None):
    """Inner-outline polygon of a tapered segment along +y (pivot frame).
    top/bot: 'round' (semicircle centred on the end point) or 'cap' (flat with chamfers).
    bot_k < 1 flattens the bottom round into a half-ellipse (depth bot_k * r)."""
    def hw(y):
        return lerp(hw_top, hw_bot, (y - y_top) / (y_bot - y_top))

    pts = []
    if top == 'round':
        cy = y_top if top_center is None else top_center
        r = hw(cy)
        pts += arc(0, cy, r, 180, 360, n)  # left -> over the top -> right
    else:
        c = chamfer
        pts += [(-hw(y_top) + c, y_top), (hw(y_top) - c, y_top), (hw(y_top + c), y_top + c)]
    if bot == 'joint':
        # hidden joint end: straight sides down to j_in above the pivot (y_bot), then the hull of a small
        # circle (radius r_j) round the pivot, so a deeply bent joint shows no knob past the band
        j_in, r_j = joint
        ye = y_bot - j_in
        he = hw(ye)
        dist = math.hypot(he, j_in)
        phi_t = math.degrees(math.atan2(-j_in, he) + math.acos(r_j / dist))
        pts += [(he, ye)] + arc(0, y_bot, r_j, phi_t, 180 - phi_t, n) + [(-he, ye)]
    elif bot == 'round':
        cy = y_bot if bot_center is None else bot_center
        r = hw(cy)
        pts += [(hw(cy), cy)] + [(x, cy + (y - cy) * bot_k) for (x, y) in arc(0, cy, r, 0, 180, n)[1:]]
    else:
        c = chamfer
        pts += [(hw(y_bot - c), y_bot - c), (hw(y_bot) - c, y_bot), (-hw(y_bot) + c, y_bot), (-hw(y_bot - c), y_bot - c)]
    if top != 'round':
        pts += [(-hw(y_top + chamfer), y_top + chamfer)]
    return pts


# ---------------------------------------------------------------- legs
FRONT = dict(
    L1=317.0, L2=388.0, hoofH=125.0,
    upper_top=-81.0,           # outer top of the visible cap (near front)
    w_top=211.0, w_knee=171.0, # outer widths of the upper: at cap top, at band top
    band=(197.0, 126.0),       # outer w,h centred on the knee pivot
    cannon=168.0,
    hoof=(177.0, 177.0, 0.0),  # outer width top, bottom, forward flare offset of the front edge
)
HIND = dict(
    L1=421.7, L2=403.0, hoofH=126.0,
    w_top=280.0, w_knee=135.0,  # outer widths at hip, at hock pivot (reference: 218 @179, 159 @339)
    band=(168.0, 93.0),
    cannon=144.0,
    hoof=(157.0, 171.0),        # outer width top/bottom, flare forward only
)

# hidden knee / hock end of the uppers: (straight sides end this far above the pivot, inner radius of the end
# circle). The circle stays inside the band's half height at any bend, so no knob pokes out past the band.
JOINT_FRONT = (30.0, FRONT['band'][1] / 2 - OL - 3)
JOINT_HIND = (24.0, HIND['band'][1] / 2 - OL - 3)


def upper_front(near=True, s=1.0):
    F = FRONT
    hw_cap = F['w_top'] * s / 2 - OL
    band_top = F['L1'] - F['band'][1] / 2
    hw_bt = F['w_knee'] * s / 2 - OL
    y_top = F['upper_top'] + OL
    # linear taper through the cap top and the band top
    def hw(y):
        return lerp(hw_cap, hw_bt, (y - y_top) / (band_top - y_top))
    if near:
        P = taper_seg(hw(y_top), hw(F['L1']), y_top, F['L1'], top='cap', bot='joint', chamfer=16, joint=JOINT_FRONT)
        y0 = y_top - OL
    else:
        # hidden under the chest: tall rounded top so the slanted chest edge always covers it
        yt = -100.0
        P = taper_seg(hw(yt), hw(F['L1']), yt, F['L1'], top='round', bot='joint', joint=JOINT_FRONT)
        y0 = yt - hw(yt) - OL
    r_bot = hw(F['L1'])
    cv = Canvas(-hw_cap - OL - 4, y0, hw_cap + OL + 4, F['L1'] + JOINT_FRONT[1] + OL + 2)
    bevel_block(cv.ctx, P, SEG_STYLE)
    return cv


def lower_front(s=1.0):
    F = FRONT
    bw, bh = F['band'][0] * s, F['band'][1]
    hwc = F['cannon'] * s / 2 - OL
    L2 = F['L2']
    cv = Canvas(-bw / 2 - 2, -bh / 2 - 2, bw / 2 + 2, L2 + hwc + OL)
    ctx = cv.ctx
    cannon = [(-hwc, 0), (hwc, 0)] + [(hwc, L2)] + arc(0, L2, hwc, 0, 180, 28)[1:]
    bevel_block(ctx, cannon, dict(SEG_STYLE, bw=dict(up=0, left=17, right=33, down=13)))
    # soft cast shadow of the band on the cannon
    y_sh = bh / 2
    ctx.save()
    path_poly(ctx, [(-hwc, 0), (hwc, 0), (hwc, L2), (-hwc, L2)])
    ctx.clip()
    import cairo
    g = cairo.LinearGradient(0, y_sh, 0, y_sh + 16)
    g.add_color_stop_rgba(0, *c255(UNDER_BAND_SHADOW), 0.55)
    g.add_color_stop_rgba(1, *c255(UNDER_BAND_SHADOW), 0.0)
    ctx.rectangle(-hwc, y_sh - 2, 2 * hwc, 20)
    ctx.set_source(g)
    ctx.fill()
    ctx.restore()
    band = chamfer_rect(-bw / 2 + OL, -bh / 2 + OL, bw / 2 - OL, bh / 2 - OL, 12)
    bevel_block(ctx, band, BAND_STYLE)
    return cv


def hoof_piece(kind='front', s=1.0):
    if kind == 'front':
        wt, wb, _ = FRONT['hoof']
        H = FRONT['hoofH']
        wt *= s; wb *= s
        x0, x1t, x1b = -wt / 2, wt / 2, wb / 2
        ch = (0, 0, 8, 6)
    else:
        wt, wb = HIND['hoof']
        H = HIND['hoofH']
        wt *= s; wb *= s
        back = -HIND['cannon'] * s / 2  # flush with the cannon's back edge
        x0 = back
        x1t = back + wt
        x1b = back + wb
        ch = (0, 0, 12, 6)
    P = [(x0 + OL, OL), (x1t - OL, OL), (x1b - OL, H - OL - ch[2]), (x1b - OL - ch[2], H - OL), (x0 + OL + ch[3], H - OL), (x0 + OL, H - OL - ch[3])]
    cv = Canvas(x0 - 2, -2, max(x1t, x1b) + 2, H + 2)
    bevel_block(cv.ctx, P, HOOF_STYLE)
    return cv


def upper_hind(s=1.0):
    Hd = HIND
    hw0 = Hd['w_top'] * s / 2 - OL
    hw1 = Hd['w_knee'] * s / 2 - OL
    P = taper_seg(hw0, hw1, 0.0, Hd['L1'], top='round', bot='joint', joint=JOINT_HIND)
    cv = Canvas(-hw0 - OL - 2, -hw0 - OL - 2, hw0 + OL + 2, Hd['L1'] + JOINT_HIND[1] + OL + 2)
    bevel_block(cv.ctx, P, SEG_STYLE)
    return cv


def lower_hind(s=1.0):
    Hd = HIND
    bw, bh = Hd['band'][0] * s, Hd['band'][1]
    hwc = Hd['cannon'] * s / 2 - OL
    L2 = Hd['L2']
    cv = Canvas(-bw / 2 - 2, -bh / 2 - 26, bw / 2 + 2, L2 + hwc + OL)
    ctx = cv.ctx
    cannon = [(-hwc, 0), (hwc, 0)] + [(hwc, L2)] + arc(0, L2, hwc, 0, 180, 28)[1:]
    bevel_block(ctx, cannon, dict(SEG_STYLE, bw=dict(up=0, left=17, right=31, down=13)))
    import cairo
    y_sh = bh / 2
    ctx.save()
    path_poly(ctx, [(-hwc, 0), (hwc, 0), (hwc, L2), (-hwc, L2)])
    ctx.clip()
    g = cairo.LinearGradient(0, y_sh, 0, y_sh + 14)
    g.add_color_stop_rgba(0, *c255(UNDER_BAND_SHADOW), 0.55)
    g.add_color_stop_rgba(1, *c255(UNDER_BAND_SHADOW), 0.0)
    ctx.rectangle(-hwc, y_sh - 2, 2 * hwc, 18)
    ctx.set_source(g)
    ctx.fill()
    ctx.restore()
    # hock band with the point of the hock (small lit wedge on the back-top corner)
    x0, x1 = -bw / 2 + OL, bw / 2 - OL
    y0, y1 = -bh / 2 + OL, bh / 2 - OL
    band = [(x0 + 22, y0 - 16), (x0 + 58, y0), (x1 - 10, y0), (x1, y0 + 10), (x1, y1 - 10), (x1 - 10, y1), (x0 + 10, y1), (x0, y1 - 10), (x0, y0 + 6)]
    bevel_block(ctx, band, BAND_STYLE)
    # the point of the hock catches the light: near-white cream facet (reference ~ (252,238,222))
    fill_poly(ctx, [(x0 + 22, y0 - 16), (x0 + 54, y0 + 1), (x0 + 30, y0 + 15), (x0 + 1, y0 + 8)], HOCK_HL)
    return cv


# ---------------------------------------------------------------- tail
TAIL_PIVOT = (120.0, 1230.0)  # root pivot on the 2048 canvas, under the rump
TAIL = dict(
    left_face=(65, 48, 40), left_hl=(90, 67, 56), left_dark=(36, 24, 17),
    right_face=(53, 41, 34), right_shade=(35, 30, 26), right_hl=(64, 50, 43),
)


def _round_corners(poly, radii, n=10):
    """Replace selected vertices by circular fillets: radii[i] (0 = keep sharp)."""
    import math as _m
    out = []
    N = len(poly)
    for i in range(N):
        r = radii[i]
        p = poly[i]
        if r <= 0:
            out.append(p)
            continue
        a = poly[i - 1]
        b = poly[(i + 1) % N]
        v1 = (a[0] - p[0], a[1] - p[1])
        v2 = (b[0] - p[0], b[1] - p[1])
        l1, l2 = _m.hypot(*v1), _m.hypot(*v2)
        u1 = (v1[0] / l1, v1[1] / l1)
        u2 = (v2[0] / l2, v2[1] / l2)
        cosang = max(-1, min(1, u1[0] * u2[0] + u1[1] * u2[1]))
        ang = _m.acos(cosang)
        t = r / _m.tan(ang / 2)
        t = min(t, l1 * 0.45, l2 * 0.45)
        s0 = (p[0] + u1[0] * t, p[1] + u1[1] * t)
        s1 = (p[0] + u2[0] * t, p[1] + u2[1] * t)
        # quadratic bezier through the corner (close enough to a fillet)
        for k in range(n + 1):
            tt = k / n
            x = (1 - tt) ** 2 * s0[0] + 2 * (1 - tt) * tt * p[0] + tt ** 2 * s1[0]
            y = (1 - tt) ** 2 * s0[1] + 2 * (1 - tt) * tt * p[1] + tt ** 2 * s1[1]
            out.append((x, y))
    return out


def tail_shapes():
    """Tail polygons in canvas coordinates (inner edge of the outline)."""
    P = [(-3.0, 1180.0), (200.0, 1180.0), (200.0, 1330.0), (76.6, 1440.0), (65.5, 1560.0), (65.5, 1996.5),
         (-124.0, 1996.5), (-124.0, 1819.0), (-203.8, 1819.0), (-203.8, 1422.3)]
    P = _round_corners(P, [26, 0, 60, 30, 0, 10, 8, 0, 10, 48])
    divider = [(118.0, 1140.0), (49.4, 1220.0), (-100.0, 1404.0), (-100.0, 1830.0)]
    left_region = [(-3.0, 1180.0), (118.0, 1180.0), (118.0, 1140.0), (49.4, 1220.0), (-100.0, 1404.0), (-100.0, 1819.0),
                   (-203.8, 1819.0), (-203.8, 1422.3)]
    left_contour = [(130.0, 1180.0), (-3.0, 1180.0), (-203.8, 1422.3), (-203.8, 1819.0)]
    right_edge = [(200.0, 1330.0), (76.6, 1440.0), (65.5, 1560.0), (65.5, 2000.0)]
    step_edge = [(-124.0, 1819.0), (-124.0, 2000.0)]
    return P, divider, left_region, left_contour, right_edge, step_edge


def tail_piece():
    import cairo
    px, py = TAIL_PIVOT
    P, divider, left_region, left_contour, right_edge, step_edge = tail_shapes()
    loc = lambda pts: [(x - px, y - py) for (x, y) in pts]  # noqa: E731
    P, divider, left_region = loc(P), loc(divider), loc(left_region)
    left_contour, right_edge, step_edge = loc(left_contour), loc(right_edge), loc(step_edge)
    xs = [p[0] for p in P]
    ys = [p[1] for p in P]
    cv = Canvas(min(xs) - OL, min(ys) - OL, max(xs) + OL, max(ys) + OL)
    ctx = cv.ctx
    T = TAIL
    outline(ctx, P)

    def stroke_poly(pts, width, col, closed=False):
        ctx.new_path()
        ctx.move_to(*pts[0])
        for p in pts[1:]:
            ctx.line_to(*p)
        if closed:
            ctx.close_path()
        ctx.set_source_rgb(*c255(col))
        ctx.set_line_width(width)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()

    ctx.save()
    path_poly(ctx, P)
    ctx.clip()
    # right (inner) strand
    fill_poly(ctx, P, T['right_face'])
    stroke_poly(right_edge, 2 * 64, T['right_shade'])
    # shade near the root (under the rump)
    g = cairo.LinearGradient(0, 1300 - py, 0, 1470 - py)
    g.add_color_stop_rgba(0, *c255(T['right_shade']), 1)
    g.add_color_stop_rgba(1, *c255(T['right_shade']), 0)
    ctx.rectangle(-400, 1100 - py, 800, 400)
    ctx.set_source(g)
    ctx.fill()
    stroke_poly(step_edge, 2 * 9, T['right_hl'])
    # left (outer) strand
    ctx.save()
    path_poly(ctx, left_region)
    ctx.clip()
    fill_poly(ctx, left_region, T['left_face'])
    stroke_poly(left_contour, 2 * 16, T['left_hl'])
    stroke_poly(left_contour, 2 * 3, T['left_dark'])
    ctx.restore()
    # divider between the strands
    stroke_poly(divider, 11, (13, 8, 5))
    ctx.restore()
    return cv
