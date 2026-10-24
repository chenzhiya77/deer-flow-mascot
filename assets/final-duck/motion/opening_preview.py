"""The opening with the final duck and the new horse as one continuous preview: every frame of the opening's
timeline, from the duck perched on the book tower to the two of them galloping out of frame.

The duck is the opening's duckPose (characters/duckMotion.ts) ported line by line. Where the opening reads its
own horse (seatWorld, bodyFrame().pitch) the port reads the new one: the hero leap lands on the new saddle and
the riding spring is driven by the new saddle's motion. The horse is keyframes.horse_state (the leg / tail /
neck rig of ../../horse-legs at preview time T - 1.9) plus the opening's back dip when the duck lands on it.
The camera is the opening's: camX / camY / camZ and the hand-held drift of lib/story.tsx (no impact shakes, no
roll), and the video runs in real time through the opening's speed ramp (slow motion at the leap's apex), at
the opening's 60 fps. Stage, book tower, shadows and duck size as keyframes.py. Layering: on the tower the duck
is behind the horse, from the hop on in front of it, and split at its middle (right half behind the horse,
left half in front) from the frame its right boot reaches the horse on the way down to the saddle.

Usage:
  python opening_preview.py                       # -> <repo>/out/final-duck-opening/opening-preview.mp4
  python opening_preview.py --still 2.35 4.9      # stills at these story times -> out/final-duck-opening/T2.35.png ...
  python opening_preview.py --jobs 2 --fps 30 --clean
  python opening_preview.py --check dump.json     # the port vs the opening's own numbers (opening_dump.mts)
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import keyframes as KF  # noqa: E402  (world, horse, stage; also the duck rig and the horse-legs modules)

D, GP, PV, GT, G, R = KF.D, KF.GP, KF.PV, KF.GT, KF.G, KF.R
PXU, W, H = KF.PXU, KF.W, KF.H
OUT = os.path.join(PV.OUT_DIR, 'final-duck-opening')


# ---------------------------------------------------------------- lib/math.ts
def clamp(v, lo=0.0, hi=1.0):
    return min(hi, max(lo, v))


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(a, b, v):
    t = 0.0 if b == a else clamp((v - a) / (b - a))
    return t * t * (3 - 2 * t)


def ease_out_cubic(t):
    return 1 - (1 - clamp(t)) ** 3


def ease_out_quad(t):
    return 1 - (1 - clamp(t)) * (1 - clamp(t))


def ring(t, freq, decay):
    return 0.0 if t <= 0 else math.exp(-decay * t) * math.sin(2 * math.pi * freq * t)


def hermite(keys, t):
    """Cubic Hermite through (t, v, d) keys; holds before the first key, extrapolates linearly after the last."""
    if t <= keys[0][0]:
        return keys[0][1]
    if t >= keys[-1][0]:
        return keys[-1][1] + (keys[-1][2] or 0.0) * (t - keys[-1][0])
    i = 0
    while i < len(keys) - 2 and t > keys[i + 1][0]:
        i += 1
    (t0, v0, d0), (t1, v1, d1) = keys[i], keys[i + 1]
    h = t1 - t0
    s = (t - t0) / h
    if d0 is None:
        d0 = (v1 - keys[i - 1][1]) / (t1 - keys[i - 1][0]) if i > 0 else (v1 - v0) / h
    if d1 is None:
        d1 = (keys[i + 2][1] - v0) / (keys[i + 2][0] - t0) if i + 2 < len(keys) else (v1 - v0) / h
    s2, s3 = s * s, s * s * s
    return (2 * s3 - 3 * s2 + 1) * v0 + (s3 - 2 * s2 + s) * h * d0 + (-2 * s3 + 3 * s2) * v1 + (s3 - s2) * h * d1


def _hash(n):
    s = math.sin(n * 127.1 + 311.7) * 43758.5453123
    return s - math.floor(s)


def fbm1(x, seed=0.0, octaves=3):
    a, total, norm, fx = 0.5, 0.0, 0.0, x
    for o in range(octaves):
        sd = seed + o * 3.7
        i = math.floor(fx)
        f = fx - i
        u = f * f * (3 - 2 * f)
        total += a * (lerp(_hash(i + sd * 17.13), _hash(i + 1 + sd * 17.13), u) * 2 - 1)
        norm += a
        a *= 0.5
        fx *= 2.03
    return total / norm


# ---------------------------------------------------------------- lib/timeline.ts (story seconds, opening units)
FPS = 60
BEAT = dict(duckNotice=1.55, duckCrouch=2.05, drop=2.35, hopEnd=2.47, land=3.0, peelOut=3.28, runStart=3.42,
            runEnd=4.18, takeoff=4.26, mount=4.9, gaitStart=5.0, gaitEnd=5.75, onward=5.12, camStop=6.05, end=10.2)
WALK_V, GALLOP_V = 349.0, 1400.0
SLOW_APEX, SLOW_HALF, SLOW_MIN = 4.766, 0.42, 0.3
_KS = 1 - SLOW_MIN
_CR = SLOW_APEX + _KS * SLOW_HALF / 2


def real_to_story(t):
    """Speed ramp: video seconds -> story seconds (slow motion around the leap's apex)."""
    w = SLOW_HALF
    if t <= _CR - w:
        return t
    if t >= _CR + w:
        return t - _KS * w
    u = (t - _CR) / w
    return t - _KS * w * ((u + 1) / 2 + math.sin(math.pi * u) / (2 * math.pi))


def time_speed(t):
    u = (t - _CR) / SLOW_HALF
    return 1.0 if abs(u) >= 1 else 1 - _KS * (1 + math.cos(math.pi * u)) / 2


def story_to_real(s):
    lo, hi = s, s + _KS * SLOW_HALF + 0.01
    for _ in range(50):
        m = (lo + hi) / 2
        if real_to_story(m) < s:
            lo = m
        else:
            hi = m
    return (lo + hi) / 2


_RUSH = None


def cam_x(T):
    global _RUSH
    if T <= 3.0:
        return 0.0
    if T <= 4.9:
        return hermite(((3.0, 0.0, 0.0), (3.75, 131.0, WALK_V), (4.9, 532.35, WALK_V)), T)
    if _RUSH is None:     # riders' screen x during the camera's rush & brake
        _RUSH = ((4.9, KF.horse_x(4.9) - 532.35, 0.0), (5.55, 660.0, 0.0), (BEAT['camStop'], 950.0, GALLOP_V))
    tt = min(T, BEAT['camStop'])
    return KF.horse_x(tt) - hermite(_RUSH, tt)


def cam_y(T):
    fall = 24 * smoothstep(2.62, 3.05, T) * (1 - smoothstep(3.25, 3.95, T))
    return fall - 14 * math.sin(math.pi * clamp((T - 4.26) / 0.7))


def cam_z(T, tr):
    push = lerp(-0.035, 0.016, smoothstep(0, 2.5, T))
    pull = lerp(0, -0.05, smoothstep(5.0, 6.1, T))
    slow_push = 0.032 * ((1 - time_speed(tr)) / _KS)
    settle = lerp(0, 0.05, smoothstep(5.6, 7.4, T))
    return push + pull + slow_push + settle


def camera(tr):
    """Story time and the opening's camera (lib/story.tsx computeStory, without shakes and roll) at video time tr."""
    T = real_to_story(tr)
    return T, (cam_x(T) + fbm1(T * 0.35, 1) * 7, cam_y(T) + fbm1(T * 0.3, 2) * 4.5, cam_z(T, tr))


def cam_view(cam):
    """World (2048 horse canvas) -> frame px through the opening's projection of its character plane (z = 1)."""
    x, y, z = cam
    d = 1 - z
    k, tx, ty = 1 / d, -x / d, -y / d
    return np.array([[k / PXU, 0, W / 2 - W / 2 * k + tx],
                     [0, k / PXU, H / 2 + (KF.GROUND_V - G.GROUND / PXU - H / 2) * k + ty], [0, 0, 1.]])


# ---------------------------------------------------------------- horses: the new one, and the opening's (for --check)
def dip(T):
    """The opening's back dip when the duck lands on the saddle (horseRig.ts bodyFrame), opening units."""
    return 7 * ring(T - BEAT['mount'], 2.6, 6)


def new_seat(T):
    """Seat (saddle dip, keyframes.SEAT_C) of the new horse at story time T, opening units."""
    p = PV.params(T - KF.T_SHIFT)
    sx, sy = D.apply(KF.body(p, dip(T)), *KF.SEAT_C)
    return (sx + KF.wx(KF.horse_x(T) + 2) - KF.SEAT_C[0]) / PXU, KF.GROUND_V + (sy - G.GROUND) / PXU


def new_pitch(T):
    return PV.params(T - KF.T_SHIFT)['pitch']


_ODT = 1 / 600
_OPHI = [0.18]
for _i in range(int(11.2 / _ODT) + 2):
    _T = _i * _ODT
    _g = smoothstep(5.0, 5.55, _T)
    _OPHI.append(_OPHI[-1] + lerp(WALK_V, GALLOP_V, smoothstep(5.0, 5.75, _T)) * lerp(0.62, 0.32, _g) / lerp(140, 150, _g) * _ODT)


def _old_body(T):
    f = max(T, 0.0) / _ODT
    i = int(f)
    phi = _OPHI[i] + (_OPHI[i + 1] - _OPHI[i]) * (f - i)
    g = smoothstep(5.0, 5.55, T)
    bob = lerp(2.6 * math.cos(4 * math.pi * phi), -11 * math.cos(2 * math.pi * (phi - 0.95)), g)
    pitch = lerp(1.0 * math.sin(4 * math.pi * phi), -4.6 * math.sin(2 * math.pi * (phi + 0.03)), g)
    return bob + dip(T), pitch


def old_seat(T):
    """The opening's seatWorld (old horse: SEAT (2, -277) about PIVOT (0, -215))."""
    bob, pitch = _old_body(T)
    c, s = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    dx, dy = 2.0, -277.0 + 215.0
    return KF.horse_x(T) + dx * c - dy * s, KF.GROUND_V + bob - 215 + dx * s + dy * c


def old_pitch(T):
    return _old_body(T)[1]


# ---------------------------------------------------------------- characters/duckMotion.ts
PERCH, HOP_X, LANE, TO_X, APEX_Y = (700.0, 395.0), 712.0, 866.0, 1100.0, 548.0
HOP_T, HANG_T, DROP_T, LAND_T = BEAT['drop'], BEAT['hopEnd'], 2.66, BEAT['land']
HOP_RISE, HANG_DY = 42.0, 22.0
Y_HANG0 = PERCH[1] - HOP_RISE
V_HANG = 2 * HANG_DY / (DROP_T - HANG_T)
Y_DROP0 = Y_HANG0 + HANG_DY
A_DROP = (LANE - Y_DROP0 - V_HANG * (LAND_T - DROP_T)) / (LAND_T - DROP_T) ** 2
TO_T, MOUNT_T, VX_LEAP = BEAT['takeoff'], BEAT['mount'], 775.0
RUN_KEYS = ((LAND_T, HOP_X, 0.0), (BEAT['peelOut'], HOP_X, 0.0), (BEAT['runStart'], HOP_X + 10, 260.0), (TO_T, TO_X, VX_LEAP))
STRIDE, PH_DT, PH_T0 = 64.0, 1 / 600, BEAT['peelOut']
RD_DT = 1 / 600


def run_x(T):
    return hermite(RUN_KEYS, T)


def run_v(T):
    return (run_x(T + 0.002) - run_x(T - 0.002)) / 0.004


def _blink(T, times):
    return any(b < T < b + 0.11 for b in times)


class DuckMotion:
    """duckPose on a given horse: seat(T) -> (u, v), pitch(T) -> deg (opening units, story seconds)."""

    def __init__(self, seat, pitch):
        self.seat, self.pitch = seat, pitch
        # leg cycle phase of the chase, integrated so feet never skate
        n = math.ceil((TO_T + 0.1 - PH_T0) / PH_DT) + 2
        self.PH = np.zeros(n)
        p = 0.0
        for i in range(n):
            self.PH[i] = p
            T = PH_T0 + i * PH_DT
            p += max(13.0 if T < BEAT['runStart'] else 0.0, run_v(T) / STRIDE) * PH_DT
        # the hero leap: ballistic from the take-off point to the seat at the mount beat
        Dl = MOUNT_T - TO_T
        ex, ey = seat(MOUNT_T)
        h1, h2 = LANE - APEX_Y, ey - APEX_Y
        t_up = Dl * math.sqrt(h1) / (math.sqrt(h1) + math.sqrt(h2))
        g = 2 * h1 / (t_up * t_up)
        self.leap = dict(D=Dl, end=(ex, ey), tUp=t_up, g=g, vy0=-g * t_up, cx=(ex - TO_X - VX_LEAP * Dl) / (Dl * Dl))
        # riding: secondary-motion spring driven by the seat's acceleration
        n = math.ceil((BEAT['end'] + 0.5 - MOUNT_T) / RD_DT) + 3
        P = [seat(MOUNT_T + i * RD_DT) for i in range(-1, n + 1)]      # P[i + 1] = seat at step i
        w = 2 * math.pi * 5.0
        kk, c = w * w, 2 * 0.36 * w
        lp = self.leap_pos(Dl)
        v0 = ((P[2][0] - P[1][0]) / RD_DT, (P[2][1] - P[1][1]) / RD_DT)
        ox = oy = 0.0
        vx, vy = lp[2] - v0[0], (lp[3] - v0[1]) * 0.8
        self.OX, self.OY, self.AX = np.zeros(n), np.zeros(n), np.zeros(n)
        for i in range(n):
            p0, p1, p2 = P[i], P[i + 1], P[i + 2]
            ax = (p2[0] - 2 * p1[0] + p0[0]) / (RD_DT * RD_DT)
            ay = (p2[1] - 2 * p1[1] + p0[1]) / (RD_DT * RD_DT)
            self.OX[i], self.OY[i], self.AX[i] = ox, oy, ax
            vx += (-kk * ox - c * vx - ax) * RD_DT
            vy += (-kk * oy - c * vy - ay) * RD_DT
            ox += vx * RD_DT
            oy += vy * RD_DT
        self.RD_N = n

    def run_phase(self, T):
        f = clamp((T - PH_T0) / PH_DT, 0, len(self.PH) - 2)
        i = int(f)
        return self.PH[i] + (self.PH[i + 1] - self.PH[i]) * (f - i)

    def leap_pos(self, tau):
        L = self.leap
        return (TO_X + VX_LEAP * tau + L['cx'] * tau * tau, LANE + L['vy0'] * tau + 0.5 * L['g'] * tau * tau,
                VX_LEAP + 2 * L['cx'] * tau, L['vy0'] + L['g'] * tau)

    def ride(self, arr, T):
        f = clamp((T - MOUNT_T) / RD_DT, 0, self.RD_N - 2)
        i = int(f)
        return arr[i] + (arr[i + 1] - arr[i]) * (f - i)

    def ride_accel(self, T):
        return sum(self.ride(self.AX, T + j * 0.02) for j in range(-8, 9)) / 17

    def pose(self, T):
        p = dict(x=PERCH[0], y=PERCH[1], rot=0.0, sx=1.0, sy=1.0, head=0.0, wingN=4.0, wingF=6.0, spread=0.0,
                 flap=0.0, legs='stand', legPhase=0.0, spin=0.0, eye='open', lx=0.8, ly=0.0, beak=0.0, vx=0.0,
                 vy=0.0, sit=0.0, stars=0.0, sweat=0.0)
        if T < BEAT['duckCrouch']:                        # A. perched, reading the stream; notices the horse
            br = math.sin(2 * math.pi * 0.75 * T)
            p['sy'], p['sx'] = 1 + 0.014 * br, 1 - 0.01 * br
            reading = smoothstep(0.35, 0.6, T) * (1 - smoothstep(BEAT['duckNotice'] - 0.05, BEAT['duckNotice'] + 0.08, T))
            p['lx'], p['ly'] = lerp(0.35, 1, smoothstep(0.45, 1.5, T)), -0.1
            p['head'] = -3 + 1.6 * math.sin(2 * math.pi * 1.7 * T) * reading
            if _blink(T, (0.95, 1.42)):
                p['eye'] = 'blink'
            if T >= BEAT['duckNotice']:
                u = T - BEAT['duckNotice']
                look = smoothstep(0, 0.1, u)
                p['lx'], p['ly'] = lerp(p['lx'], -0.35, look), lerp(p['ly'], 0.95, look)
                p['head'] = lerp(p['head'], 13, smoothstep(0, 0.14, u)) + 4 * ring(u - 0.02, 3.2, 6)
                p['eye'] = 'shock' if u < 0.09 else 'sparkle' if u < 0.27 else 'determined'
                hop = math.sin(math.pi * (u - 0.08) / 0.18) if 0.08 < u < 0.26 else 0.0
                p['y'] -= 11 * hop
                p['sy'] *= 1 + 0.06 * hop
                p['wingN'] += 26 * hop
                p['wingF'] += 22 * hop
                p['legs'] = 'tuck' if hop > 0 else 'stand'
            return p
        if T < HOP_T:                                     # B. crouch (anticipation + butt wiggle)
            u = (T - BEAT['duckCrouch']) / (HOP_T - BEAT['duckCrouch'])
            e = ease_out_cubic(u)
            p['sy'], p['sx'] = 1 - 0.16 * e, 1 + 0.09 * e
            p['rot'] = 9 * e + 3.2 * math.sin(2 * math.pi * 7 * T) * smoothstep(0.15, 0.4, u) * (1 - smoothstep(0.75, 0.95, u))
            p['head'], p['wingN'], p['wingF'] = 12 - 4 * e, 4 + 14 * e, 6 + 12 * e
            p.update(eye='determined', lx=0.25, ly=1.0, legs='crouch')
            return p
        if T < HANG_T:                                    # C. hop off the tower
            u = (T - HOP_T) / (HANG_T - HOP_T)
            p['x'] = lerp(PERCH[0], HOP_X, ease_out_cubic(u))
            p['y'] = PERCH[1] - HOP_RISE * ease_out_quad(u)
            p['sy'] = lerp(1.2, 1.0, u)
            p['sx'] = 1 / p['sy'] ** 0.6
            p['rot'] = lerp(9, -5, u)
            p['wingN'], p['wingF'] = lerp(18, 72, ease_out_cubic(u)), lerp(16, 66, ease_out_cubic(u))
            p.update(spread=u, eye='happy', legs='tuck', vx=130.0, vy=-200 * (1 - u))
            return p
        if T < DROP_T:                                    # D. cartoon hang-time: flap like mad, realise
            u = (T - HANG_T) / (DROP_T - HANG_T)
            p['x'], p['y'] = HOP_X, Y_HANG0 + HANG_DY * u * u
            p['wingN'] = 58 + 44 * math.sin(2 * math.pi * 13 * (T - HANG_T))
            p['wingF'] = 52 + 40 * math.sin(2 * math.pi * 13 * (T - HANG_T) - 0.5)
            p.update(spread=1.0, flap=1.0, rot=-3 + 3 * math.sin(2 * math.pi * 6 * T), legs='run',
                     legPhase=(T - HANG_T) * 14, spin=1.0, eye='shock', lx=0.1 if u < 0.5 else 0.0,
                     ly=1.0 if u < 0.5 else 0.0, head=10.0 if u < 0.5 else 0.0, beak=0.45,
                     sweat=smoothstep(0.45, 0.6, u), vy=V_HANG * u)
            return p
        if T < LAND_T:                                    # E. the drop (vertical)
            tau = T - DROP_T
            vy = V_HANG + 2 * A_DROP * tau
            p['x'], p['y'] = HOP_X, Y_DROP0 + V_HANG * tau + A_DROP * tau * tau
            p['sy'] = 1 + min(0.3, vy / 7000)
            p['sx'] = 1 / math.sqrt(p['sy'])
            p['wingN'] = lerp(70, 118, smoothstep(0, 0.09, tau)) + 6 * math.sin(2 * math.pi * 9 * tau)
            p['wingF'] = lerp(64, 112, smoothstep(0, 0.1, tau)) + 6 * math.sin(2 * math.pi * 9 * tau + 1)
            p.update(spread=1.0, legs='dangle', eye='squeeze' if LAND_T - T < 0.07 else 'shock', lx=0.0, ly=-0.9,
                     head=-8.0, beak=0.85, sweat=1 - smoothstep(0, 0.12, tau), vy=vy)
            return p
        if T < BEAT['peelOut']:                           # F. landing: squash, dizzy, double-take
            tau = T - LAND_T
            s = 0.44 * math.exp(-10 * tau) * math.cos(2 * math.pi * 3.6 * tau)
            p['x'], p['y'], p['sy'], p['sx'] = HOP_X, LANE, 1 - s, 1 + 0.62 * s
            p['wingN'] = lerp(118, 6, smoothstep(0, 0.07, tau)) + 16 * ring(tau - 0.05, 4, 9)
            p['wingF'] = lerp(112, 8, smoothstep(0, 0.08, tau)) + 14 * ring(tau - 0.06, 4, 9)
            p['spread'] = 1 - smoothstep(0, 0.1, tau)
            p['legs'] = 'crouch' if tau < 0.2 else 'stand'
            p['stars'] = smoothstep(0.0, 0.03, tau) * (1 - smoothstep(0.16, 0.22, tau))
            p['eye'] = 'squeeze' if tau < 0.1 else 'shock' if tau < 0.19 else 'determined'
            p['lx'], p['ly'] = (0.0 if tau < 0.1 else 1.0), 0.0
            p['head'] = (-10 * math.sin(2 * math.pi * (tau - 0.1) / 0.08) * math.exp(-14 * (tau - 0.1))
                         if 0.1 < tau < 0.26 else 0.0)
            p['rot'] = 10 * smoothstep(0.18, 0.28, tau)
            p['beak'] = 0.5 if 0.1 < tau < 0.18 else 0.0
            return p
        if T < TO_T:                                      # G / H / I. peel-out, chase, crouch
            v, ph = run_v(T), self.run_phase(T)
            p.update(x=run_x(T), y=LANE, vx=v, legPhase=ph, eye='determined', lx=1.0, ly=-0.1)
            if T < BEAT['runStart']:                      # wheel-spin in place
                p.update(legs='run', spin=1.0, rot=20.0, sy=0.95, sx=1.04, wingN=24.0, wingF=20.0)
                p['y'] -= 2 * abs(math.sin(2 * math.pi * ph))
            elif T < BEAT['runEnd']:
                p['legs'] = 'run'
                p['spin'] = clamp(1 - (T - BEAT['runStart']) / 0.12) * 0.8
                p['rot'] = 12 + 8 * clamp(v / VX_LEAP)
                p['y'] -= 6 * abs(math.sin(2 * math.pi * ph))
                p['sy'], p['sx'] = 1 + 0.04 * math.cos(4 * math.pi * ph), 1 - 0.03 * math.cos(4 * math.pi * ph)
                p['wingN'], p['wingF'] = 22 + 22 * math.sin(2 * math.pi * ph), 20 - 20 * math.sin(2 * math.pi * ph)
                p['head'] = -2 + 3 * math.sin(4 * math.pi * ph)
            else:
                u = (T - BEAT['runEnd']) / (TO_T - BEAT['runEnd'])
                p.update(legs='crouch', sy=1 - 0.22 * ease_out_quad(u), sx=1 + 0.12 * u, rot=lerp(20, 24, u),
                         wingN=lerp(22, -8, u), wingF=lerp(20, -6, u), eye='sparkle' if u > 0.6 else 'determined',
                         ly=-0.5)
            return p
        if T < MOUNT_T:                                   # J. the hero leap (slow-mo apex)
            tau = T - TO_T
            x, y, vx, vy = self.leap_pos(tau)
            p.update(x=x, y=y, vx=vx, vy=vy)
            p['sy'] = 1 + 0.24 * math.exp(-7 * tau)
            p['sx'] = 1 / p['sy'] ** 0.7
            p['rot'] = clamp(math.degrees(math.atan2(vy, vx)) * 0.42, -24, 10)
            up = smoothstep(0, 0.16, tau)
            glide = 64 + 16 * math.sin(2 * math.pi * 3.4 * (tau - 0.3)) * smoothstep(0.26, 0.36, tau)
            p['wingN'], p['wingF'] = lerp(-8, glide, up), lerp(-6, glide - 6, up)
            p['spread'], p['flap'] = smoothstep(0.04, 0.2, tau), 0.3 * up
            p['legs'] = 'tuck' if tau < 0.5 else 'dangle'
            p['eye'] = 'determined' if tau < 0.12 else 'sparkle' if tau < 0.55 else 'happy'
            p['lx'], p['ly'], p['head'] = 1.0, (-0.4 if tau < 0.4 else 0.6), (-8.0 if tau < 0.4 else 6.0)
            p['beak'] = 0.4 * smoothstep(0.3, 0.38, tau) * (1 - smoothstep(0.5, 0.58, tau))
            return p
        sx_, sy_ = self.seat(T)                           # K. riding (spring + inertia + "onward!")
        ox, oy, ax = self.ride(self.OX, T), self.ride(self.OY, T), self.ride_accel(T)
        tau = T - MOUNT_T
        squash = clamp(oy / 30, -0.25, 0.3)
        p.update(legs='sit', sit=smoothstep(0, 0.08, tau), x=sx_ + ox, y=sy_ + min(0.0, oy), sy=1 - squash,
                 sx=1 + squash * 0.6, rot=-0.0042 * ax + 0.5 * ox + self.pitch(T),
                 vx=349 + (1400 - 349) * smoothstep(BEAT['gaitStart'], BEAT['gaitEnd'], T), vy=0.0)
        on = smoothstep(BEAT['onward'], BEAT['onward'] + 0.12, T) * (1 - smoothstep(BEAT['gaitEnd'] - 0.1, BEAT['gaitEnd'] + 0.1, T))
        flutter = 6 * math.sin(2 * math.pi * 4.2 * T)
        p['wingN'] = lerp(lerp(60, 14, smoothstep(0, 0.14, tau)), 148 + 6 * math.sin(2 * math.pi * 2.4 * T), on) + flutter * (1 - on)
        p['wingF'] = lerp(54, 18, smoothstep(0, 0.14, tau)) + 10 * on + flutter
        p['spread'] = lerp(1 - smoothstep(0, 0.16, tau), 0.85, on)
        p['eye'] = 'squeeze' if tau < 0.12 else 'determined' if on > 0.3 else 'happy'
        p['lx'], p['ly'] = 1.0, 0.0
        p['head'] = -4 * on + 4 * ring(tau, 3, 7)
        p['beak'] = 0.55 + 0.25 * math.sin(2 * math.pi * 5 * T) if on > 0.3 else 0.0
        return p


DUCK_NEW = DuckMotion(new_seat, new_pitch)


# ---------------------------------------------------------------- one frame
FRONT_T = HOP_T      # duck in front of the horse from the hop off the tower on
SPLIT_T = 4.83       # seated split from here: the right boot first touches the horse at 4.832 (60 fps frame 305)
TOWER_V = PERCH[1]
BEATS = [(0.0, '站在书堆上读字'), (BEAT['duckNotice'], '发现马'), (BEAT['duckCrouch'], '蹲下蓄力'), (HOP_T, '跳下书堆'),
         (HANG_T, '空中一顿'), (DROP_T, '下落'), (LAND_T, '落地，回头'), (BEAT['peelOut'], '原地起跑'),
         (BEAT['runStart'], '追马'), (BEAT['runEnd'], '蹲下起跳'), (TO_T, '飞跃上马'), (MOUNT_T, '落到马鞍上'),
         (BEAT['onward'], '喊“出发！”，马换步'), (BEAT['gaitEnd'], '跑出画面')]


def rig_pose(T, dp):
    """Opening pose (units) -> duckrig pose (world px). 'determined' while looking down -> the final duck's xiakan."""
    d = {k: dp[k] for k in ('rot', 'sx', 'sy', 'head', 'wingN', 'wingF', 'spread', 'legs', 'legPhase', 'lx', 'ly',
                            'beak', 'vx', 'vy', 'sit')}
    d['eye'] = 'xiakan' if dp['eye'] == 'determined' and dp['ly'] >= 0.5 else dp['eye']
    d.update(x=KF.wx(dp['x']), y=KF.wy(dp['y']) - (KF.SEAT_CLEAR if T >= MOUNT_T else 0.0), k=KF.KD, T=T)
    d['ground'] = KF.wy(TOWER_V) if T < HOP_T else KF.wy(LANE) if LAND_T <= T < TO_T else None
    return d


def duck_shadows(T, d):
    """(on the ground, on the tower top): the opening's two duck shadows, drawn like keyframes.duck_shadow."""
    ground, top = [], []
    if T < HOP_T + 0.2:
        a = clamp(1 - max(0.0, KF.wy(TOWER_V) - d['y']) / (180 * PXU)) * (1 - clamp((T - HOP_T) / 0.12))
        if a > 0:
            top.append((d['x'], KF.wy(TOWER_V), 330 * (0.6 + 0.4 * a), 30, 230 * a))
    if HOP_T < T < MOUNT_T:
        a = clamp(1 - max(0.0, KF.wy(LANE) - d['y']) / (180 * PXU))
        if a > 0:
            ground.append((d['x'], KF.wy(LANE) + 3 * PXU / 5.7, 330 * (0.6 + 0.4 * a), 30, 230 * a))
    return ground, top


_views = {}


def horse_view(V):
    """gait_preview.View with pieces prescaled to the camera scale, quantised to 0.4 % steps (M carries the rest)."""
    q = round(math.log(V[0, 0]) / math.log(1.004))
    if q not in _views:
        if len(_views) > 6:
            _views.clear()
        _views[q] = GP.View(1.004 ** q, (0, 0), (0, 0), (W, H))
    v = _views[q]
    return v


def layers(T, V):
    """Everything of one frame: (stage rgb, [(name, premultiplied layer)] back to front, duck pose)."""
    st = KF.horse_state(T - KF.T_SHIFT, dip(T))
    dxh = KF.wx(KF.horse_x(T) + 2) - KF.SEAT_C[0]
    d = rig_pose(T, DUCK_NEW.pose(T))
    img = np.empty((H, W, 3), np.float32)
    img[:] = KF.BG
    KF.ground(img, V)
    sg, stop = duck_shadows(T, d)
    KF.shadows(img, V, KF.horse_shadows(st, dxh) + sg)
    tw = KF.tower(V)
    KF.over(img, tw)
    if stop:
        KF.shadows(img, V, stop, clip=tw[..., 3:4])
    hv = horse_view(V)
    hv.M = V @ D.T3(dxh, 0)
    horse = GP.render_view(hv, st)
    if T < FRONT_T:
        ls = [('duck', KF.DUCK.render(V, d, (W, H))), ('horse', horse)]
    elif T < SPLIT_T:
        ls = [('horse', horse), ('duck', KF.DUCK.render(V, d, (W, H)))]
    else:
        ls = [('far', KF.DUCK.render(V, d, (W, H), part='far')), ('horse', horse),
              ('near', KF.DUCK.render(V, d, (W, H), part='near'))]
    return img, ls, d


f_lab = PV.font(PV.FONT_MED, 26)


def frame(tr, label=True):
    T, cam = camera(tr)
    img, ls, _ = layers(T, cam_view(cam))
    for _, L in ls:
        KF.over(img, L)
    im = Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))
    if label:
        name = [n for t0, n in BEATS if T >= t0][-1]
        sp = time_speed(tr)
        txt = f'{name}   T = {T:.2f} s' + (f'   慢放 ×{sp:.2f}' if sp < 0.995 else '')
        ImageDraw.Draw(im).text((34, 26), txt, font=f_lab, fill=PV.GRAY)
    return im


# ---------------------------------------------------------------- render
END_T = 7.0          # story time: the riders are out of frame


def frame_bytes(args):
    tr, label = args
    return frame(tr, label).tobytes()


def check(path):
    """Port vs the opening (opening_dump.mts): duckPose on the opening's own horse, camera, speed ramp."""
    ref = json.load(open(path, encoding='utf-8'))
    old = DuckMotion(old_seat, old_pitch)
    num = ('x', 'y', 'rot', 'sx', 'sy', 'head', 'wingN', 'wingF', 'spread', 'flap', 'legPhase', 'spin', 'lx', 'ly',
           'beak', 'vx', 'vy', 'sit', 'stars', 'sweat')
    err = {k: 0.0 for k in num + ('seatX', 'seatY', 'pitch', 'horseX')}
    bad = 0
    for r in ref['poses']:
        T = r['T']
        p = old.pose(T)
        bad += any(p[k] != r[k] for k in ('legs', 'eye'))
        for k in num:
            err[k] = max(err[k], abs(p[k] - r[k]))
        sx, sy = old_seat(T)
        err['seatX'], err['seatY'] = max(err['seatX'], abs(sx - r['seatX'])), max(err['seatY'], abs(sy - r['seatY']))
        err['pitch'] = max(err['pitch'], abs(old_pitch(T) - r['pitch']))
        err['horseX'] = max(err['horseX'], abs(KF.horse_x(T) - r['horseX']))
    cerr = dict(T=0.0, x=0.0, y=0.0, z=0.0, hx=0.0, hy=0.0)
    for c in ref['cams']:
        T = real_to_story(c['t'])
        hx, hy = fbm1(T * 0.35, 1) * 7, fbm1(T * 0.3, 2) * 4.5
        for k, v in (('T', T), ('x', cam_x(T)), ('y', cam_y(T)), ('z', cam_z(T, c['t'])), ('hx', hx), ('hy', hy)):
            cerr[k] = max(cerr[k], abs(v - c[k]))
    print(f'{len(ref["poses"])} poses, legs / eye mismatches: {bad}')
    print('max |port - opening|:', ', '.join(f'{k} {v:.2e}' for k, v in err.items()))
    print(f'{len(ref["cams"])} frames, camera:', ', '.join(f'{k} {v:.2e}' for k, v in cerr.items()))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--still', type=float, nargs='+', metavar='T', help='stills at these story times (s)')
    ap.add_argument('--fps', type=int, default=FPS)
    ap.add_argument('--jobs', type=int, default=2)
    ap.add_argument('--clean', action='store_true', help='no caption')
    ap.add_argument('--out')
    ap.add_argument('--check', metavar='DUMP', help='compare the port with opening_dump.mts output, then exit')
    a = ap.parse_args()
    if a.check:
        check(a.check)
        return
    os.makedirs(OUT, exist_ok=True)
    if a.still:
        for T in a.still:
            p = os.path.join(OUT, f'T{T:g}.png')
            frame(story_to_real(T), not a.clean).save(p)
            print(p)
        return
    nf = int(math.ceil(story_to_real(END_T) * a.fps))
    out = a.out or os.path.join(OUT, 'opening-preview.mp4' if a.fps == FPS else f'opening-preview-{a.fps}fps.mp4')
    ff = shutil.which('ffmpeg')
    if not ff:
        sys.exit('ffmpeg not found')
    enc = subprocess.Popen([ff, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                            '-framerate', str(a.fps), '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18',
                            '-preset', 'slow', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    from multiprocessing import Pool
    with Pool(max(1, a.jobs)) as pool:
        for n, buf in enumerate(pool.imap(frame_bytes, [(i / a.fps, not a.clean) for i in range(nf)])):
            enc.stdin.write(buf)
            if n % 60 == 0:
                print(f'{n}/{nf}', flush=True)
    enc.stdin.close()
    if enc.wait():
        sys.exit('ffmpeg failed')
    print(out)


if __name__ == '__main__':
    main()
