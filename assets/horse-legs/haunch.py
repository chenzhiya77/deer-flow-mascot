"""Near hind haunch follow: the thigh drawn on the body turns with the near hind (LH) upper leg.

body.png has the near hind thigh drawn on it: a lobe that ends about 115 px below the LH hip, its front
edge is the dark crease line. The LH upper leg turns about the hip inside this lobe; with a still lobe the
leg looks like it slides in a fixed sleeve. front(theta) warps just this part of the body piece (two-bone
skinning): every body point P turns about the LH hip by w(P) * theta,

    w = smoothstep(1420, 1720, y) * (1 - smoothstep(4, 120, d)),   d = x - crease_x(y)

so the lower lobe turns fully, and the weight fades out upwards into the rump and forwards across the crease
into the belly, which stays put. The art's lines and shading stay continuous: nothing is cut or redrawn.
angle() follows the leg by FOLLOW, softly limited to +-LIMIT.

Canvas constants (CREASE, the weight ranges, ROI) are measured on the current body placement.
"""
import math
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(os.path.dirname(HERE), 'horse-upper', 'motion'))
import gen as G  # noqa: E402
import rig as R  # noqa: E402  (neck/mane rig: body / saddle frame, RS, c2f)

FOLLOW = 0.5   # share of the LH upper leg angle (relative to the body, from its rest angle) the haunch follows
LIMIT = 20.0   # soft limit of the haunch angle (deg): LIMIT * tanh(raw / LIMIT)
PIVOT = np.array(G.LEGS['LH']['root'], float)
REST = G.rest_angles(G.LEGS['LH'])[0]
# thigh crease (front edge of the drawn lobe), canvas (y, x) traced on body.png
CREASE = np.array([(1430, 527), (1600, 529), (1620, 526), (1640, 523), (1660, 518), (1680, 511), (1700, 503),
                   (1720, 492), (1740, 481), (1760, 469), (1780, 457), (1800, 446), (1820, 430)], float)
TOP, BAND = (1420, 1720), (4, 120)  # weight fade: upwards (canvas y) and across the crease (d, canvas px)
ROI = (40, 1380, 800, 1960)  # canvas box that may change (x0, y0, x1, y1)


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def weight(X, Y):
    d = X - np.interp(Y, CREASE[:, 0], CREASE[:, 1])
    return smooth(*TOP, Y) * (1 - smooth(*BAND, d))


def angle(legs, pitch):
    """Haunch angle (deg, clockwise) for gait.poses() legs and the body pitch."""
    raw = FOLLOW * ((legs['LH']['a_up'] - pitch) - REST)
    return LIMIT * math.tanh(raw / LIMIT) if LIMIT > 0 else raw


_f0 = [int(round(v)) for v in R.c2f(ROI[0], ROI[1])]
_f1 = [int(round(v)) for v in R.c2f(ROI[2], ROI[3])]
FX0, FY0 = max(0, _f0[0]), max(0, _f0[1])
FX1, FY1 = min(R.FW, _f1[0]), min(R.FH, _f1[1])
_jj, _ii = np.mgrid[FY0:FY1, FX0:FX1].astype(np.float32)
QX = R.FX0 + _ii / R.RS  # canvas coords of the ROI's frame pixels (same convention as R.c2f)
QY = R.FY0 + _jj / R.RS


def turn(x, y, deg):
    c, s = np.cos(np.radians(deg)), np.sin(np.radians(deg))
    dx, dy = x - PIVOT[0], y - PIVOT[1]
    return PIVOT[0] + c * dx - s * dy, PIVOT[1] + s * dx + c * dy


def source_map(theta):
    """Inverse of the warp Q = turn(P, w(P) theta) by fixed-point iteration: canvas source P per ROI pixel."""
    px, py = QX, QY
    for _ in range(6):
        px, py = turn(QX, QY, -theta * weight(px, py))
    return px, py


def front(theta):
    """Body + saddle layer (premultiplied, rig frame) with the haunch turned by theta degrees."""
    if abs(theta) < 1e-3:
        return R.front_f
    px, py = source_map(theta)
    mx = ((px - R.FX0) * R.RS).astype(np.float32)
    my = ((py - R.FY0) * R.RS).astype(np.float32)
    body = cv2.remap(R.body_f, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    sad = R.saddle_f[FY0:FY1, FX0:FX1]
    out = R.front_f.copy()
    out[FY0:FY1, FX0:FX1] = body * (1 - sad[..., 3:4]) + sad
    return out


def jacobian_min(theta, step=2):
    """Smallest Jacobian determinant of the forward warp over the body in the ROI: > 0 means no fold."""
    X, Y = QX[::step, ::step].astype(np.float64), QY[::step, ::step].astype(np.float64)
    body = R.body_f[FY0:FY1:step, FX0:FX1:step, 3] > 0.01

    def fwd(x, y):
        return turn(x, y, theta * weight(x, y))

    e = 0.5
    ax, ay = fwd(X + e, Y)
    bx, by = fwd(X - e, Y)
    cx, cy = fwd(X, Y + e)
    dx, dy = fwd(X, Y - e)
    return float((((ax - bx) * (cy - dy) - (ay - by) * (cx - dx)) / (4 * e * e))[body].min())


if __name__ == '__main__':
    for th in (-LIMIT, -10.0, 10.0, LIMIT):
        print(f'theta {th:+5.1f}  min Jacobian {jacobian_min(th):.3f}')
