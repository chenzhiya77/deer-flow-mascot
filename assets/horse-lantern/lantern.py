"""马灯 for the new horse: the opening's hurricane lantern, ported with only the hanging point changed.

Sources (harness-rag-opening): src/desert/lantern.ts (the swing) and HorseLantern / LampPool / LampBloom /
nightGrade in src/characters/Characters.tsx (the drawing). Lengths in "opening units" (1 unit = 1 world px of
the 1920x1080 opening) unless a name says px.

Swing (lantern.ts, same numbers): a damped pendulum hanging from a pivot on the saddle, driven by the real
acceleration of that pivot (gait bob, pitch, the walk -> gallop surge), simulated once on a fixed step and cached:
  L th'' = -a_x cos th - (g - a_y) sin th,  minus damping on th',  th clamped to +-1.2 rad (y down, + = forward).
Drawing: the opening's vector lamp ('svg', every path and colour as in Characters.tsx) or the same lamp with this
pack's ink outline ('ink'); the warm pool on the ground, the bloom round the glass and the night grade (cool colour
matrix + moonlight rim from the upper right) for the riders. S scales the opening's sizes onto the 2048 canvas.
"""
import math

import cairo
import cv2
import numpy as np

OPEN = dict(pivot=(54, -256), L=30, g=2450, damp=2.1)  # lantern.ts (pivot: old horse body frame, unused here)
PIVOT = (1250.0, 1395.0)  # canvas px, body-local: ring on the saddle's front-bottom chamfer (on its outline)
S = 6.0                   # canvas px per opening unit for the lamp, its light and the rim (old barrel 334 units ~ new body 1895 px)
DT, FD, TH0, TH_MAX = 1 / 480, 1 / 40, 0.05, 1.2  # sim step / finite-difference span / start angle / clamp (lantern.ts)
SOFT_KY = 0.25            # softened swing: share of the pivot's vertical acceleration the lamp feels (lantern.ts: 1)
OL = 15.0                 # ink outline, canvas px (horse-legs render.OL)
INK = (13 / 255, 8 / 255, 5 / 255)


def clamp(x, a, b):
    return max(a, min(b, x))


def lerp(a, b, t):
    return a + (b - a) * t


# ---------------------------------------------------------------- flicker (lib/math.ts hash / noise1 / fbm1)
def _hash(n):
    s = math.sin(n * 127.1 + 311.7) * 43758.5453123
    return s - math.floor(s)


def noise1(x, seed=0.0):
    i = math.floor(x)
    f = x - i
    u = f * f * (3 - 2 * f)
    return lerp(_hash(i + seed * 17.13), _hash(i + 1 + seed * 17.13), u) * 2 - 1


def fbm1(x, seed=0.0, octaves=3):
    a, total, norm, fx = 0.5, 0.0, 0.0, x
    for o in range(octaves):
        total += a * noise1(fx, seed + o * 3.7)
        norm += a
        a *= 0.5
        fx *= 2.03
    return total / norm


def flick(T):
    """Flame brightness 0.64..1 (lanternState().flick)."""
    return 0.82 + 0.12 * fbm1(T * 9, 3) + 0.06 * math.sin(T * 31)


# ---------------------------------------------------------------- swing
class Swing:
    """theta(T) of the lantern.ts pendulum; pivot_at(T) -> world pivot (x, y) in opening units.
    ky < 1 softens it: the gallop bob lifts the pivot at up to ~1.8 g, so with ky = 1 the effective gravity
    (g - a_y) flips sign every stride at about twice the lamp's own frequency (parametric resonance) and the
    lamp slams into the +-1.2 rad clamp - in the opening too. ky = SOFT_KY keeps the gallop within ~+-30 deg.
    pre > 0 starts the run pre s early (constant pivot velocity), so the start-up kick is gone by T = 0."""

    def __init__(self, pivot_at, t_max, L=OPEN['L'], g=OPEN['g'], damp=OPEN['damp'], ky=1.0, pre=0.0):
        n = int(math.ceil(t_max / DT)) + 2
        th = np.empty(n)
        theta, omega = TH0, 0.0
        if pre > 0:  # run in from T = -pre at the pivot's T = 0 velocity: the lamp is settled at T = 0
            p0 = np.array(pivot_at(0.0), float)
            v0 = (np.array(pivot_at(1e-3), float) - p0) / 1e-3
            P = lambda T: pivot_at(T) if T >= 0 else tuple(p0 + T * v0)  # noqa: E731
        else:  # lantern.ts: bodyFrame(max(0, T)) - at rest at T = 0 although the horse already walks
            P = lambda T: pivot_at(max(0.0, T))  # noqa: E731
        for i in range(-int(round(pre / DT)), n):
            T = i * DT
            a, b, c = P(T - FD), P(T), P(T + FD)
            ax = (c[0] - 2 * b[0] + a[0]) / (FD * FD)
            ay = (c[1] - 2 * b[1] + a[1]) / (FD * FD)
            alpha = (-ax * math.cos(theta) - (g - ky * ay) * math.sin(theta)) / L - damp * omega
            omega += alpha * DT
            theta = clamp(theta + omega * DT, -TH_MAX, TH_MAX)
            if i >= 0:
                th[i] = theta
        self.th, self.t_max = th, t_max

    def __call__(self, T):
        f = clamp(T, 0.0, self.t_max) / DT
        i = min(len(self.th) - 2, int(math.floor(f)))
        return float(lerp(self.th[i], self.th[i + 1], f - i))


# ---------------------------------------------------------------- drawing (cairo, premultiplied)
def rgb(h, a=1.0):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)) + (a,)


def _stops(g, stops, k=1.0):
    for off, col, a in stops:
        r, gg, b, _ = rgb(col)
        g.add_color_stop_rgba(off, r, gg, b, a * k)
    return g


def _quad(ctx, p0, q, p2):
    ctx.move_to(*p0)
    ctx.curve_to(p0[0] + 2 / 3 * (q[0] - p0[0]), p0[1] + 2 / 3 * (q[1] - p0[1]),
                 p2[0] + 2 / 3 * (q[0] - p2[0]), p2[1] + 2 / 3 * (q[1] - p2[1]), *p2)


def _rrect(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


def _ellipse(ctx, cx, cy, rx, ry):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(rx, ry)
    ctx.new_sub_path()
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()


def _stroke(ctx, col, w, a=1.0):
    ctx.set_source_rgba(*rgb(col, a))
    ctx.set_line_width(w)
    ctx.stroke()


def _fill(ctx, col, a=1.0):
    ctx.set_source_rgba(*rgb(col, a))
    ctx.fill()


GLASS = [(0, '#FFF4C8', 1), (0.45, '#FFC766', 1), (1, '#D9782E', 1)]
GLOW = [(0, '#FFD58E', 0.62), (0.32, '#FFA650', 0.2), (1, '#FF8A3A', 0)]
POOL = [(0, '#FFC27A', 0.55), (0.5, '#E89A5A', 0.2), (1, '#C77A4A', 0)]


def _flame(ctx, f):
    y0 = 5 - 3 * f
    ctx.move_to(0, y0)
    ctx.curve_to(3.4, 9, 3.2, 15, 0, 17.5)
    ctx.curve_to(-3.2, 15, -3.4, 9, 0, y0)
    ctx.close_path()


def _glass(ctx):
    ctx.set_source(_stops(cairo.RadialGradient(-2, 11, 0, 0, 13, 13), GLASS))
    _ellipse(ctx, 0, 14, 10, 12.5)
    ctx.fill()


def lamp_svg(ctx, f, L=OPEN['L']):
    """HorseLantern, path for path (lamp frame: pivot at 0, hanging along +y, opening units)."""
    ctx.set_line_cap(cairo.LINE_CAP_BUTT)
    ctx.move_to(0, -2)
    ctx.line_to(0, L - 7)
    _stroke(ctx, '#171827', 1.7)
    _quad(ctx, (-10, L + 6), (0, L - 12), (10, L + 6))
    _stroke(ctx, '#2A2B40', 1.5)
    ctx.translate(0, L)
    _glass(ctx)
    _flame(ctx, f)
    _fill(ctx, '#FFF8E2', 0.95)
    for x, y0, y1 in ((-9.5, 5, 23), (9.5, 5, 23), (-4.5, 2, 26), (4.5, 2, 26)):
        ctx.move_to(x, y0)
        ctx.line_to(x, y1)
    _stroke(ctx, '#2B2638', 1.2, 0.85)
    for x, y in ((-9, 3), (9, 3), (6, -4), (-6, -4)):
        ctx.line_to(x, y)
    ctx.close_path()
    _fill(ctx, '#3B3448')
    _rrect(ctx, -3, -8, 6, 4, 1.2)
    _fill(ctx, '#4A4258')
    _rrect(ctx, -11, 24, 22, 6, 2.2)
    _fill(ctx, '#3B3448')
    ctx.rectangle(-11, 24, 22, 1.7)
    _fill(ctx, '#FFC58A', 0.7)
    ctx.move_to(6, -4)
    ctx.line_to(9, 3)
    _stroke(ctx, '#FFD49A', 1.0, 0.6)


METAL, METAL_HI = '#4A4044', '#86766F'


def _inked(ctx, path, fill, ow):
    """This pack's outline: ink stroked 2*ow on the shape edge (ow shows outside), then the fill inside."""
    path()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(2 * ow)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke_preserve()
    ctx.fill()
    path()
    if isinstance(fill, str):
        _fill(ctx, fill)
    else:
        ctx.set_source(fill)
        ctx.fill()


def lamp_ink(ctx, f, L=OPEN['L'], ow=OL / S):
    """Same lamp shapes and glass / flame / warm rim colours, drawn the way the horse pieces are: thick dark
    outline, flat metal with a light top edge, a glint on the glass; the outer cage bars sit in the outline."""
    ink = '#0D0805'
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(0, 0)
    ctx.line_to(0, L - 7)
    _stroke(ctx, ink, 0.55 * ow)
    _quad(ctx, (-10, L + 6), (0, L - 12), (10, L + 6))
    _stroke(ctx, ink, 0.62 * ow)
    ctx.translate(0, L)
    _inked(ctx, lambda: _ellipse(ctx, 0, 14, 10, 12.5), _stops(cairo.RadialGradient(-2, 11, 0, 0, 13, 13), GLASS), ow)
    _flame(ctx, f)
    _fill(ctx, '#FFF8E2', 0.95)
    for x in (-4.5, 4.5):
        ctx.move_to(x, 3)
        ctx.line_to(x, 25)
    _stroke(ctx, ink, 0.42 * ow)
    ctx.arc(0, 14, 7.0, math.radians(200), math.radians(250))   # glint, upper left of the glass
    _stroke(ctx, '#FFFBEA', 0.32 * ow, 0.85)

    def cap():
        for x, y in ((-9, 3), (9, 3), (6, -4), (-6, -4)):
            ctx.line_to(x, y)
        ctx.close_path()
    _inked(ctx, cap, METAL, ow)
    ctx.move_to(-5.2, -2.6)
    ctx.line_to(5.2, -2.6)
    _stroke(ctx, METAL_HI, 0.3 * ow)
    _inked(ctx, lambda: _rrect(ctx, -3, -8, 6, 4, 1.2), METAL, ow * 0.8)
    _inked(ctx, lambda: _rrect(ctx, -11, 24, 22, 6, 2.2), METAL, ow)
    ctx.rectangle(-10, 24.2, 20, 1.6)
    _fill(ctx, '#FFC58A', 0.75)


def ring_ink(ctx, ow=OL / S):
    """Small D-ring on the saddle the ink lamp hangs from (body-fixed)."""
    _inked(ctx, lambda: ctx.arc(0, 0, 2.6, 0, 2 * math.pi), METAL, 0.55 * ow)
    ctx.arc(0, 0, 1.1, 0, 2 * math.pi)
    _fill(ctx, '#0D0805')


def draw_lamp(ctx, x, y, th, f, s, style='ink', ring=True):
    """Lamp hanging from (x, y) in surface px, swing th (rad), s = surface px per opening unit.

    style 'ink' (default) = this pack's ink outline + D-ring, 'svg' = the opening's vector lamp."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    if style == 'ink' and ring:
        ctx.save()
        ring_ink(ctx)
        ctx.restore()
    ctx.rotate(-th)
    (lamp_ink if style == 'ink' else lamp_svg)(ctx, f)
    ctx.restore()


def lamp_centre(x, y, th, s, L=OPEN['L']):
    """Glass centre (bloom / pool anchor): pivot + (L + 14)(sin th, cos th)."""
    return x + math.sin(th) * (L + 14) * s, y + math.cos(th) * (L + 14) * s


def pool(ctx, x, yg, f, s):
    """LampPool: warm ellipse on the ground under the lamp (x = glass centre x, yg = ground line)."""
    ctx.save()
    ctx.translate(x + 6 * s, yg + 12 * s)
    ctx.scale(250 * s, 34 * s)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.set_source(_stops(cairo.RadialGradient(0, 0, 0, 0, 0, 1), POOL, 0.75 * f))
    ctx.fill()
    ctx.restore()


def bloom(ctx, x, y, f, s):
    """LampBloom: two glow discs round the glass."""
    for r, k in ((380, 0.3), (120, 0.75)):
        ctx.arc(x, y, r * s, 0, 2 * math.pi)
        ctx.set_source(_stops(cairo.RadialGradient(x, y, 0, x, y, r * s), GLOW, k * f))
        ctx.fill()


def surface(w, h):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    return s, cairo.Context(s)


def to_rgba(surf):
    """cairo ARGB32 (premultiplied BGRA) -> float32 premultiplied RGBA."""
    a = np.ndarray((surf.get_height(), surf.get_stride() // 4, 4), np.uint8, surf.get_data())[:, :surf.get_width()]
    return a[..., [2, 1, 0, 3]].astype(np.float32) / 255


# ---------------------------------------------------------------- night grade (nightGrade filter)
GRADE_M = np.array([[0.86, 0.04, 0.02], [0.02, 0.88, 0.04], [0.03, 0.06, 1.0]], np.float32)
GRADE_OFF = np.array([0, 0.008, 0.03], np.float32)
RIM = np.array(rgb('#D3E2FF')[:3], np.float32)


def night_grade(layer, s):
    """feColorMatrix + moonlight rim on a premultiplied RGBA layer; s = layer px per opening unit.
    Rim: alpha minus itself shifted (-3.5, 3), blurred 0.9, flooded #D3E2FF at 0.85 -> lit upper-right edges."""
    A = layer[..., 3]
    col = np.minimum(layer[..., :3] @ GRADE_M.T + A[..., None] * GRADE_OFF, A[..., None])
    sh = cv2.warpAffine(A, np.float32([[1, 0, -3.5 * s], [0, 1, 3 * s]]), (A.shape[1], A.shape[0]),
                        flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)  # no false rim where a crop cuts the body
    edge = cv2.GaussianBlur(A * (1 - sh), (0, 0), max(0.3, 0.9 * s))
    ra = (0.85 * edge)[..., None]
    out = np.empty_like(layer)
    out[..., :3] = RIM * ra + col * (1 - ra)
    out[..., 3] = ra[..., 0] + A * (1 - ra[..., 0])
    return out
