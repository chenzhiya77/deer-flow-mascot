"""Small 2D helpers for the leg/tail generator (canvas px, y down)."""
import math


def lerp(a, b, t):
    return a + (b - a) * t


def edge_normal(p, q, cw=True):
    """Outward normal of edge p->q for a polygon listed clockwise on screen (y down)."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    L = math.hypot(dx, dy) or 1.0
    # clockwise on screen (y down) -> outward normal is (dy, -dx)
    return (dy / L, -dx / L) if cw else (-dy / L, dx / L)


def signed_area(poly):
    a = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        a += x0 * y1 - x1 * y0
    return a / 2


def ensure_cw(poly):
    # y-down screen: clockwise visually == positive shoelace area
    return poly if signed_area(poly) > 0 else poly[::-1]


def line_isect(p1, d1, p2, d2):
    """Intersection of p1 + t d1 and p2 + s d2."""
    den = d1[0] * d2[1] - d1[1] * d2[0]
    if abs(den) < 1e-9:
        return ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
    t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / den
    return (p1[0] + t * d1[0], p1[1] + t * d1[1])


def offset_poly(poly, dists):
    """Inset a clockwise polygon; dists[i] is the inward offset of edge i (poly[i]->poly[i+1]).
    Edges that would flip (short chamfers under a wide inset) collapse to a point, so the result never
    self-intersects; the output keeps one vertex per input vertex (collapsed edges -> repeated vertex)."""
    n = len(poly)
    lines = []
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        nx, ny = edge_normal(p, q)
        d = dists[i]
        lines.append(((p[0] - nx * d, p[1] - ny * d), (q[0] - p[0], q[1] - p[1])))
    alive = list(range(n))
    while True:
        m = len(alive)
        verts = {}
        for k in range(m):
            a, b = lines[alive[k - 1]], lines[alive[k]]
            verts[alive[k]] = line_isect(a[0], a[1], b[0], b[1])
        worst, worst_dot = None, 0.0
        for k in range(m):
            i, j = alive[k], alive[(k + 1) % m]
            d = lines[i][1]
            dot = ((verts[j][0] - verts[i][0]) * d[0] + (verts[j][1] - verts[i][1]) * d[1]) / (math.hypot(*d) or 1.0)
            if dot < worst_dot - 1e-6:
                worst, worst_dot = i, dot
        if worst is None or m <= 3:
            break
        alive.remove(worst)
    out = []
    for i in range(n):
        k = i
        while k not in verts:
            k = (k + 1) % n
        out.append(verts[k])
    return out


def arc(cx, cy, r, a0, a1, n=24):
    """Points on a circle from angle a0 to a1 (degrees, y-down screen angles)."""
    pts = []
    for i in range(n + 1):
        a = math.radians(lerp(a0, a1, i / n))
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def chamfer_rect(x0, y0, x1, y1, c):
    """Clockwise octagon (screen) with corner chamfer c; c may be a 4-tuple (tl,tr,br,bl)."""
    if not isinstance(c, (tuple, list)):
        c = (c, c, c, c)
    tl, tr, br, bl = c
    return [(x0 + tl, y0), (x1 - tr, y0), (x1, y0 + tr), (x1, y1 - br), (x1 - br, y1), (x0 + bl, y1), (x0, y1 - bl), (x0, y0 + tl)]


def dedupe(poly, eps=1e-6):
    out = []
    for p in poly:
        if not out or math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > eps:
            out.append(p)
    if len(out) > 1 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) < eps:
        out.pop()
    return out
