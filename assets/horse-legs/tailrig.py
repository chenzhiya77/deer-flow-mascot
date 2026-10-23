"""Tail chain rig: the drawn tail bends along a smooth spine driven like the opening's 10-link tail chain.

Conventions (same as the leg rig): 2048-canvas px, y down, angles in degrees clockwise from straight down.
The tail piece hangs from its pivot along the rest axis. The spine starts at the pivot; its tangent angle
theta(s) is piecewise linear in arc length s between knots (constant before the first knot and after the
last), i.e. a chain of circular arcs with a continuous tangent - bends, never kinks. Every tail pixel keeps its
arc length s and its lateral offset n (along m = (-cos, -sin)). The spine runs `n_off` px behind the pivot
axis, through the middle of the tail, so a bend squashes one edge and stretches the other about equally.
Up to the first knot the tail turns rigidly about the pivot.
"""
import math

import cv2
import numpy as np

NSEG = 10  # links of the opening's tail chain (HorseCowboy.tsx: 10 x 14u)

# motion, adapted from HorseCowboy.tsx: tailBase lerp(108,166,g), amp lerp(5,9,g), w = 2pi lerp(1.1,2.6,g),
# acc = base + 4 sin(wT); acc += amp*.55*sin(wT - .75 i) per link. Deviations from the drawn rest pose.
MOTION = dict(
    lift=50.0,          # deg the whole tail rises at full gallop (opening: +58 from 108 to 166)
    droop=20.0,         # deg the tip sinks back over `bend` at full gallop (weight of the long, wide tail)
    bend=(120.0, 620.0),  # arc-length span (px from the pivot) of the droop
    sway=4.0,           # root sway amplitude (deg)
    amp=(5.0, 9.0),     # per-link wave amplitude walk / gallop (deg, x0.55 per link like the opening)
    lag=0.75,           # wave phase lag per link (rad): the wave runs from root to tip
    freq=(1.1, 2.6),    # wave frequency walk / gallop (Hz); integrate the phase, do not multiply T
    follow=0.025,       # s of delay per link when the gait changes (root rises first, tip follows)
)


def lerp(a, b, t):
    return a + (b - a) * t


def clamp(x, a, b):
    return max(a, min(b, x))


def _d(t):
    return np.array([-math.sin(t), math.cos(t)])


def _m(t):
    return np.array([-math.cos(t), -math.sin(t)])


class Spine:
    """theta(s) through knots (s_i px, th_i deg), linear in between; passes n_off*m(th_0) at s = 0."""

    def __init__(self, s_knots, th_deg, n_off=0.0):
        self.s = [float(v) for v in s_knots]
        self.th = [math.radians(v) for v in th_deg]
        self.n_off = float(n_off)
        s, th = self.s, self.th
        c = s[0] * _d(th[0]) + self.n_off * _m(th[0])
        self.c0 = c.copy()
        self.pieces = []  # (s_a, s_b, th_a, k, C_a, K) ; K = arc centre or None for a straight piece
        for j in range(len(s) - 1):
            ds = s[j + 1] - s[j]
            k = (th[j + 1] - th[j]) / ds
            if abs(k) < 1e-8:
                self.pieces.append((s[j], s[j + 1], th[j], 0.0, c.copy(), None))
                c = c + ds * _d(th[j])
            else:
                K = c + _m(th[j]) / k
                self.pieces.append((s[j], s[j + 1], th[j], k, c.copy(), K))
                c = K - _m(th[j + 1]) / k
        self.c1 = c

    def theta(self, S):
        return np.interp(S, self.s, self.th)

    def forward(self, S, N):
        """(arc length, lateral offset from the pivot axis) -> offset from the pivot on the canvas."""
        S = np.asarray(S, np.float64)
        th = self.theta(S)
        Cx, Cy = np.empty_like(S), np.empty_like(S)
        t0, t1 = self.th[0], self.th[-1]
        z = S <= self.s[0]
        Cx[z] = self.c0[0] - (S[z] - self.s[0]) * math.sin(t0)
        Cy[z] = self.c0[1] + (S[z] - self.s[0]) * math.cos(t0)
        for sa, sb, tha, k, Ca, K in self.pieces:
            z = (S > sa) & (S <= sb)
            if K is None:
                Cx[z] = Ca[0] - (S[z] - sa) * math.sin(tha)
                Cy[z] = Ca[1] + (S[z] - sa) * math.cos(tha)
            else:  # C = K - m(theta) / k
                Cx[z] = K[0] + np.cos(th[z]) / k
                Cy[z] = K[1] + np.sin(th[z]) / k
        z = S > self.s[-1]
        Cx[z] = self.c1[0] - (S[z] - self.s[-1]) * math.sin(t1)
        Cy[z] = self.c1[1] + (S[z] - self.s[-1]) * math.cos(t1)
        n = np.asarray(N, np.float64) - self.n_off
        return Cx - n * np.cos(th), Cy - n * np.sin(th)

    def inverse(self, X, Y):
        """Canvas offsets from the pivot -> (S, N): nearest-point projection on the spine, piece by piece.
        Exact wherever |n| is below the local bend radius (no folding)."""
        X = np.asarray(X, np.float64)
        Y = np.asarray(Y, np.float64)
        S = np.zeros_like(X)
        Nn = np.zeros_like(X)
        best = np.full(X.shape, np.inf)

        def take(s_, n_, ok):
            upd = ok & (np.abs(n_) < best)
            S[upd] = s_[upd]
            Nn[upd] = n_[upd]
            best[upd] = np.abs(n_[upd])

        def line(C, t, s_ref):
            vx, vy = X - C[0], Y - C[1]
            return s_ref - vx * math.sin(t) + vy * math.cos(t), -vx * math.cos(t) - vy * math.sin(t)

        s_, n_ = line(self.c0, self.th[0], self.s[0])
        take(s_, n_, s_ <= self.s[0])
        for sa, sb, tha, k, Ca, K in self.pieces:
            if K is None:
                s_, n_ = line(Ca, tha, sa)
            else:  # P = K + (n - 1/k) m(theta); on the near branch n - 1/k has the sign of -k
                vx, vy = X - K[0], Y - K[1]
                sg = 1.0 if k < 0 else -1.0
                th_ = np.arctan2(-sg * vy, -sg * vx)
                dth = (th_ - tha + np.pi) % (2 * np.pi) - np.pi
                s_ = sa + dth / k
                n_ = sg * np.hypot(vx, vy) + 1.0 / k
            take(s_, n_, (s_ >= sa) & (s_ <= sb))
        s_, n_ = line(self.c1, self.th[-1], self.s[-1])
        take(s_, n_, s_ >= self.s[-1])
        return S, Nn + self.n_off


def ruler_spine(axis, lift, droop, s0, s1, n_off=0.0):
    """The v1 pose bend: rigid lift down to s0, one arc turning back by droop until s1, straight after."""
    return Spine([s0, s1], [axis + lift, axis + lift - droop], n_off)


def chain_spine(dev, length, axis, n_off=0.0):
    """Per-link deviations (deg) -> spine with one knot at the middle of each link."""
    return Spine([(i + 0.5) * length / len(dev) for i in range(len(dev))], [axis + d for d in dev], n_off)


def chain_dev(psi, gs, length, P=MOTION):
    """Per-link deviation from the drawn rest (deg). psi: integrated wave phase (rad);
    gs[i]: gait blend (0 walk .. 1 gallop) seen by link i, i.e. g(T - follow * i)."""
    s0, s1 = P['bend']
    out, acc = [], P['sway'] * math.sin(psi)
    for i in range(NSEG):
        g = gs[i]
        acc += lerp(*P['amp'], g) * 0.55 * math.sin(psi - P['lag'] * i)
        r = clamp(((i + 0.5) * length / NSEG - s0) / (s1 - s0), 0.0, 1.0)
        out.append(P['lift'] * g - P['droop'] * g * r + acc)
    return out


class TailRig:
    """Renders the tail piece along a Spine into a premultiplied float32 layer at any scale."""

    def __init__(self, rgba_u8, pivot, axis_deg, n_off):
        a = rgba_u8.astype(np.float32) / 255.0
        self.pm = np.concatenate([a[..., :3] * a[..., 3:4], a[..., 3:4]], 2)
        self.pivot = (float(pivot[0]), float(pivot[1]))
        self.axis = float(axis_deg)
        self.n_off = float(n_off)
        t = math.radians(axis_deg)
        self.rd, self.rm = _d(t), _m(t)
        ys, xs = np.nonzero(a[..., 3] > 0.004)
        sel = (xs % 3 == 0) & (ys % 3 == 0)
        u, v = xs[sel] - self.pivot[0], ys[sel] - self.pivot[1]
        self.sS = u * self.rd[0] + v * self.rd[1]
        self.sN = u * self.rm[0] + v * self.rm[1]
        self.length = float(self.sS.max())
        self._scaled = {}

    def scaled(self, scale):
        if scale not in self._scaled:
            if abs(scale - 1) < 1e-9:
                self._scaled[scale] = self.pm
            else:
                h, w = self.pm.shape[:2]
                self._scaled[scale] = cv2.resize(self.pm, (max(1, round(w * scale)), max(1, round(h * scale))),
                                                 interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
        return self._scaled[scale]

    def render(self, spine, target, origin, size, scale=1.0):
        """Layer of `size` (W, H); output px (x, y) centre <-> canvas origin + (x + .5) / scale - .5."""
        W, H = size
        out = np.zeros((H, W, 4), np.float32)
        PX, PY = spine.forward(self.sS, self.sN)
        to_px = lambda c, o, t: (c + t - o + 0.5) * scale - 0.5  # noqa: E731
        x0 = max(0, int(math.floor(to_px(PX.min(), origin[0], target[0]))) - 4)
        x1 = min(W, int(math.ceil(to_px(PX.max(), origin[0], target[0]))) + 5)
        y0 = max(0, int(math.floor(to_px(PY.min(), origin[1], target[1]))) - 4)
        y1 = min(H, int(math.ceil(to_px(PY.max(), origin[1], target[1]))) + 5)
        if x1 <= x0 or y1 <= y0:
            return out
        gx = origin[0] + (np.arange(x0, x1) + 0.5) / scale - 0.5 - target[0]
        gy = origin[1] + (np.arange(y0, y1) + 0.5) / scale - 0.5 - target[1]
        X, Y = np.meshgrid(gx, gy)
        S, N = spine.inverse(X, Y)
        u = self.pivot[0] + S * self.rd[0] + N * self.rm[0]
        v = self.pivot[1] + S * self.rd[1] + N * self.rm[1]
        src = self.scaled(scale)
        mx = ((u + 0.5) * scale - 0.5).astype(np.float32)
        my = ((v + 0.5) * scale - 0.5).astype(np.float32)
        interp = cv2.INTER_CUBIC if scale >= 0.999 else cv2.INTER_LINEAR
        out[y0:y1, x0:x1] = np.clip(cv2.remap(src, mx, my, interp, borderMode=cv2.BORDER_CONSTANT, borderValue=0), 0, 1)
        return out
