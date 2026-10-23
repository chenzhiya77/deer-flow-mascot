"""Leg gait for the generated legs: the opening's walk / gallop leg cycle (horseRig.ts legPoses).

Conventions as in compose.py: 2048-canvas px, y down, angles in degrees clockwise from straight down.
World = the canvas frame with the ground at gen.GROUND; the body (shoulders / hips) moves with bob and
pitch, the ground scrolls back under it at the horse's speed.

Every leg runs the same cycle, shifted by its phase offset. Stance (p < beta): the hoof is planted and
moves back with the ground. Swing: the hoof travels forward along an eased path, lifted by
sin(pi u^0.8) and curled back (front 78 deg, hind 48 deg, relative to the lower leg). A two-bone IK
with a little stretch puts shoulder / hip -> knee / hock -> fetlock on the target. Where the
stretched leg is still too short in stance, the hoof rolls over its toe (breakover, body ahead of the
hoof) or its heel (heel strike, body behind) instead of leaving the ground, and in swing the hoof is
kept above the ground. A planted hoof is locked to the scrolling ground (see Gait), so it never skates,
also while the walk blends into the gallop.
"""
import math

import numpy as np

import gen as G
import parts as P
from compose import dirv

# the opening's gait table (timeline.ts GAIT): stride S and lift in opening units, beta = stance share
GAIT = dict(
    walk=dict(S=140.0, beta=0.62, lift=34.0, off=dict(LH=0.0, LF=0.25, RH=0.5, RF=0.75)),
    gallop=dict(S=150.0, beta=0.32, lift=58.0, off=dict(LH=0.0, LF=0.45, RH=0.12, RF=0.57)),
)
UNIT = 3.5           # canvas px per opening unit for stride and lift
BOB_UNIT = 4.0       # canvas px per opening unit for the body bob (neck/mane preview: 5.8, no legs there)
CURL = dict(front=78.0, hind=48.0)  # swing hoof curl (deg)
STRETCH = 1.04       # max IK stretch of upper + lower (opening: 1.09 on its thin legs)
ROLL_MAX = 32.0      # max toe / heel roll in stance (deg)
NEUTRAL = dict(LF=30.0, RF=30.0, LH=-60.0, RH=-60.0)  # mid-stance hoof x relative to the root (px)
ORDER = ('RH', 'RF', 'LH', 'LF')


def lerp(a, b, t):
    return a + (b - a) * t


def clamp(x, a, b):
    return max(a, min(b, x))


def smooth(a, b, x):
    t = clamp((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def ease(u):
    return -(math.cos(math.pi * clamp(u, 0.0, 1.0)) - 1) / 2


def rot(v, deg):
    """Rotate vector v clockwise (screen, y down) by deg."""
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([v[0] * c - v[1] * s, v[0] * s + v[1] * c])


def ang_of(v):
    return math.degrees(math.atan2(-v[0], v[1]))


def leg_dims(key):
    leg = G.LEGS[key]
    D = P.FRONT if leg['kind'] == 'front' else P.HIND
    s = 1.0 if leg['near'] else G.FAR_W
    H = D['hoofH']
    if leg['kind'] == 'front':
        wb = D['hoof'][1] * s
        toe, heel = wb / 2 - 8, -wb / 2 + 6
    else:
        back = -D['cannon'] * s / 2
        toe, heel = back + D['hoof'][1] * s - 12, back + 6
    return dict(kind=leg['kind'], root=np.array(leg['root']), L1=D['L1'], L2=D['L2'], H=H,
                toe=np.array([toe, H]), heel=np.array([heel, H]), bend=-1 if leg['kind'] == 'front' else 1)


DIMS = {k: leg_dims(k) for k in G.LEGS}


def law(key, phi, g):
    """The opening's phase law for one leg: phase p in [0, 1), stance share beta, stride S (canvas px)."""
    W, Gl = GAIT['walk'], GAIT['gallop']
    beta = lerp(W['beta'], Gl['beta'], g)
    S = lerp(W['S'], Gl['S'], g) * UNIT
    p = (phi + lerp(W['off'][key], Gl['off'][key], g)) % 1.0
    return p, beta, S


class Gait:
    """Leg cycles over a time grid t_i = i * dt, from stride phase phi_i, gait blend g_i (0 walk, 1 gallop)
    and ground scroll X_i (canvas px the ground has moved back, increasing).

    Stance follows the opening's law (touchdown at the neutral + S/2, lift-off when p reaches beta), but the
    planted hoof is locked to the ground: it moves back exactly with X. With a fixed gait that is the law
    itself (the hoof lifts off at the neutral - S/2); while walk blends into gallop, the law's phase offsets
    and stance share change mid-stride and would make planted hooves skate, so the hoof keeps its ground
    spot and the swing makes up the difference.
    """

    def __init__(self, phi, g, ground, dt):
        self.phi, self.g, self.X = (np.asarray(a, float) for a in (phi, g, ground))
        self.dt = dt
        self.st, self.ref = {}, {}
        for key in DIMS:
            xn = DIMS[key]['root'][0] + NEUTRAL[key]
            n = len(self.phi)
            st = np.zeros(n, bool)
            ref = np.zeros(n)  # stance: sole x + ground scroll (constant per stance); swing: lift-off sole x
            for i in range(n):
                p, beta, S = law(key, self.phi[i], self.g[i])
                st[i] = p < beta
                if st[i]:
                    if i and st[i - 1]:
                        ref[i] = ref[i - 1]
                    else:  # touchdown (or start): where the law puts the hoof
                        ref[i] = xn + S / 2 - S * p / beta + self.X[i]
                elif i == 0:
                    ref[i] = xn - S / 2
                elif st[i - 1]:  # lift-off between i - 1 and i: ground spot at the crossing of p - beta
                    p0, b0, _ = law(key, self.phi[i - 1], self.g[i - 1])
                    e0, e1 = p0 - b0, p - beta
                    f = clamp(-e0 / (e1 - e0), 0.0, 1.0) if e1 != e0 else 1.0
                    ref[i] = ref[i - 1] - lerp(self.X[i - 1], self.X[i], f)
                else:
                    ref[i] = ref[i - 1]
            self.st[key], self.ref[key] = st, ref

    def _samp(self, a, t):
        f = clamp(t / self.dt, 0.0, len(a) - 1.001)
        i = int(f)
        return a[i] + (a[i + 1] - a[i]) * (f - i)

    def scroll(self, t):
        """Ground scroll at time t (canvas px the ground has moved back)."""
        return self._samp(self.X, t)

    def stance_runs(self, key, t0, t1):
        """Stance intervals (start, end) in seconds overlapping [t0, t1], from the grid."""
        i0 = max(0, int(math.floor(t0 / self.dt)))
        i1 = min(len(self.phi) - 1, int(math.ceil(t1 / self.dt)))
        st = self.st[key][i0:i1 + 1].astype(np.int8)
        if not len(st):
            return []
        d = np.diff(np.concatenate([[0], st, [0]]))
        return [((i0 + a) * self.dt, (i0 + b - 1) * self.dt) for a, b in zip(np.nonzero(d == 1)[0], np.nonzero(d == -1)[0])]

    def state(self, key, t, g):
        """Leg state at time t (g: gait blend at t). stance: x0 = sole centre x. swing: u, lift-off sole x
        x_lo, touchdown sole x x_td, lift (canvas px)."""
        p, beta, S = law(key, self._samp(self.phi, t), g)
        stance = p < beta
        i = min(int(clamp(t / self.dt, 0.0, len(self.phi) - 2)), len(self.phi) - 2)
        j = i if self.st[key][i] == stance else i + 1
        ref = self.ref[key][j]
        if stance:
            return dict(stance=True, x0=ref - self._samp(self.X, t), S=S, beta=beta, p=p)
        u = (p - beta) / (1 - beta)
        xn = DIMS[key]['root'][0] + NEUTRAL[key]
        lift = lerp(GAIT['walk']['lift'], GAIT['gallop']['lift'], g) * UNIT * math.sin(math.pi * u ** 0.8)
        return dict(stance=False, u=u, x_lo=ref, x_td=xn + S / 2, lift=lift, S=S, beta=beta, p=p)


def ik(root, target, L1, L2, bend, smax=STRETCH):
    """Two-bone IK with stretch (opening: horseRig.ts ik). Returns a_up, a_low, stretch, knee, fetlock."""
    d_v = np.asarray(target, float) - root
    d = math.hypot(*d_v)
    s = clamp(d / ((L1 + L2) * 0.995), 1.0, smax)
    A, B = L1 * s, L2 * s
    dc = clamp(d, abs(A - B) + 1, (A + B) * 0.999)
    a_t = ang_of(d_v)
    alpha = math.degrees(math.acos(clamp((A * A + dc * dc - B * B) / (2 * A * dc), -1.0, 1.0)))
    a_up = a_t + bend * alpha
    knee = root + A * np.array(dirv(a_up))
    a_low = ang_of(np.asarray(target, float) - knee)
    fet = knee + B * np.array(dirv(a_low))
    return a_up, a_low, s, knee, fet


def reach(Dm):
    return (Dm['L1'] + Dm['L2']) * 0.995 * STRETCH


def planted(hip, x0, Dm):
    """Stance: hoof planted with its sole centre under x0. Returns (fetlock target, hoof angle)."""
    F0 = np.array([x0, G.GROUND - Dm['H']])
    R = reach(Dm)
    if math.hypot(*(F0 - hip)) <= R:
        return F0, 0.0
    toe_side = hip[0] >= F0[0]   # body ahead of the hoof -> break over the toe, else land on the heel
    c = Dm['toe'] if toe_side else Dm['heel']
    Q = F0 + c                   # contact point on the ground
    sign = 1.0 if toe_side else -1.0

    def fet(th):
        return Q + rot(-c, th)

    lo, hi = 0.0, ROLL_MAX
    if math.hypot(*(fet(sign * hi) - hip)) > R:
        return fet(sign * hi), sign * hi
    for _ in range(30):
        mid = (lo + hi) / 2
        if math.hypot(*(fet(sign * mid) - hip)) > R:
            lo = mid
        else:
            hi = mid
    return fet(sign * hi), sign * hi


def above_ground(fet, ang, Dm):
    """Raise the fetlock so the hoof (rotated by ang) stays on or above the ground."""
    low = max(rot(Dm['toe'], ang)[1], rot(Dm['heel'], ang)[1])
    over = fet[1] + low - G.GROUND
    return fet - np.array([0.0, over]) if over > 0 else fet


def leg_pose(key, st, body):
    """Pose of one leg from its Gait.state. body: 3x3 body-local -> world transform. Returns dict(a_up,
    a_low, a_hoof, s, hip, knee, fet, stance, roll); angles in degrees, s = stretch of upper + lower."""
    Dm = DIMS[key]
    hip = (body @ np.array([Dm['root'][0], Dm['root'][1], 1.0]))[:2]
    if st['stance']:
        tgt, roll = planted(hip, st['x0'], Dm)
        a_up, a_low, s, knee, fet = ik(hip, tgt, Dm['L1'], Dm['L2'], Dm['bend'])
        return dict(a_up=a_up, a_low=a_low, a_hoof=roll, s=s, hip=hip, knee=knee, fet=fet, stance=True, roll=roll)
    u = st['u']
    # the swing runs from the lift-off pose to the touchdown pose (fetlock and hoof angle), so it joins
    # the stance on both ends even when the hoof is rolled over its toe or heel there
    F0, th0 = planted(hip, st['x_lo'], Dm)
    F1, th1 = planted(hip, st['x_td'], Dm)
    tgt = F0 + (F1 - F0) * ease(u) - np.array([0.0, st['lift']])
    for _ in range(3):
        a_up, a_low, s, knee, fet = ik(hip, tgt, Dm['L1'], Dm['L2'], Dm['bend'])
        ang = a_low + CURL[Dm['kind']] * math.sin(math.pi * min(1.0, u * 1.15))
        ang = lerp(th0, ang, smooth(0.0, 0.2, u))
        ang = lerp(ang, th1, smooth(0.8, 1.0, u))
        t2 = above_ground(tgt, ang, Dm)
        if abs(t2[1] - tgt[1]) < 0.25:
            break
        tgt = t2
    return dict(a_up=a_up, a_low=a_low, a_hoof=ang, s=s, hip=hip, knee=knee, fet=fet, stance=False, roll=0.0)


def poses(gait, t, g, body):
    return {k: leg_pose(k, gait.state(k, t, g), body) for k in DIMS}
