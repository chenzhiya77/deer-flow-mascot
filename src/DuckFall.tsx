import { AbsoluteFill, useCurrentFrame } from "remotion";

import { DuckRig, type DuckPoseSpec } from "./CowboyCutUser";

// —— 单次掉落砸地起身（120f/30fps）——
// f0–8    初始正常状态：高处站定（正常姿），一次自然眨眼
// f8–18   失衡前兆：渐强摇摆（摆到零位处交出）→ 微向落侧倾（预备）
// f18–46  坠落：严格二次加速（零速起步、越掉越快），速度拉伸 sy=1+0.10u，
//         四肢上扬拖曳（慢摆，不乱挥）——物理逻辑：加速、拖尾、姿态大体稳定
// f46     触地（速度最大）
// f46–64  缓冲：快压 sy 0.86（3f）→ 短停 → 微过冲 1.05 → 1.0（不夸张、不起跳）
// f56–90  摔懵衰减倾（±2°两次收敛）＋手脚缓慢回落
// f90–120 归位站定（与 f0 同态），尾部自然眨眼
type FallKey = { f: number; sy: number; rot: number; arm: number; leg: number };

const FALL_START = 18;
const IMPACT = 46;
const TY_STAND = -980; // 高处站位：脚离地 490px（S=0.5），全身入画

const CUSHION: FallKey[] = [
  { f: IMPACT, sy: 1.1, rot: 0, arm: -55, leg: 18 },
  { f: 49, sy: 0.86, rot: 1.5, arm: 22, leg: -6 },
  { f: 52, sy: 0.87, rot: 1.2, arm: 18, leg: -5 },
  { f: 58, sy: 1.05, rot: 2.2, arm: -8, leg: 3 },
  { f: 64, sy: 0.985, rot: -1.4, arm: 6, leg: -2 },
  { f: 72, sy: 1.02, rot: 0.7, arm: -3, leg: 1 },
  { f: 80, sy: 1, rot: -0.25, arm: 2, leg: 0 },
  { f: 90, sy: 1, rot: 0, arm: 0, leg: 0 },
  { f: 120, sy: 1, rot: 0, arm: 0, leg: 0 },
];

const sample = (f: number): FallKey => {
  const keys = CUSHION;
  if (f <= keys[0].f) return keys[0];
  for (let i = 0; i < keys.length - 1; i++) {
    const a = keys[i];
    const b = keys[i + 1];
    if (f >= a.f && f <= b.f) {
      const t = (f - a.f) / (b.f - a.f);
      const e = t * t * (3 - 2 * t);
      return {
        f,
        sy: a.sy + (b.sy - a.sy) * e,
        rot: a.rot + (b.rot - a.rot) * e,
        arm: a.arm + (b.arm - a.arm) * e,
        leg: a.leg + (b.leg - a.leg) * e,
      };
    }
  }
  return keys[keys.length - 1];
};

// 取景：S=0.5 给下落留天（上站位全身入画、下落地贴阴影线）
const S = 0.5;
const BBOX = { x0: -246, y0: 37 };
const TARGET_X = (1856 - 1360 * S) / 2;
const TARGET_Y = 516; // ty=0 时脚底＝1150（阴影线）

export const DuckFall = () => {
  const f = useCurrentFrame();

  let ty: number;
  let sy: number;
  let rot: number;
  let arm: number;
  let leg: number;

  if (f < FALL_START) {
    // 高处正常站定：前 8f 完全中性，随后失衡摇摆渐强（摆幅在零位收束交出）
    const ramp = Math.max(0, (f - 8) / 10);
    ty = TY_STAND;
    sy = 1;
    rot = Math.sin(ramp * Math.PI * 2) * 2.5 * ramp;
    arm = Math.sin(f * 0.7) * 1.5;
    leg = 0;
  } else if (f < IMPACT) {
    // 二次加速下落：u² 位移（零速起步）；拉伸/拖曳随速度线性增大
    const u = (f - FALL_START) / (IMPACT - FALL_START);
    ty = TY_STAND * (1 - u * u);
    sy = 1 + 0.1 * u;
    rot = Math.sin(u * Math.PI * 1.5) * 2;
    arm = -40 - 15 * u + Math.sin(f * 0.9) * 5;
    leg = 10 + 8 * u + Math.sin(f * 0.9 + Math.PI) * 4;
  } else {
    const k = sample(f);
    ty = 0;
    sy = k.sy;
    rot = k.rot;
    arm = k.arm;
    leg = k.leg;
  }

  // 自然眨眼（开场站定、收尾各一次）
  const blinkDip = (c: number) => {
    const d = Math.abs(f - c);
    return d === 0 ? 0.12 : d === 1 ? 0.5 : 1;
  };
  const blink = Math.min(blinkDip(5), blinkDip(111));

  const airborne = f < IMPACT;
  const spec: DuckPoseSpec = {
    body: { ty, sy, sx: 1 / sy, rot },
    local: {
      eye_0: { sy: blink },
      eye_1: { sy: blink },
      boot_l: { rot: leg, org: "50% 0%" },
      boot_r: { rot: leg * 0.85, org: "50% 0%" },
      hand_0: { rot: arm, org: "50% 0%" },
      hand_1: { rot: arm * 0.9, org: "50% 0%" },
    },
    // 触地后脚钉地面（压扁时身向脚压实），空中随身走
    planted: airborne ? [] : ["boot_l", "boot_r"],
  };
  return (
    <AbsoluteFill style={{ backgroundColor: "#FFFFFF" }}>
      <svg viewBox="0 0 1856 1280" width="100%" height="100%" style={{ position: "absolute" }}>
        <ellipse cx={928} cy={1150} rx={220} ry={14} fill="#EFE6D2" />
      </svg>
      <div
        style={{
          position: "absolute",
          inset: 0,
          transformOrigin: "0 0",
          transform: `translate(${TARGET_X - BBOX.x0 * S}px, ${TARGET_Y - BBOX.y0 * S}px) scale(${S})`,
        }}
      >
        <DuckRig pose="rest" spec={spec} />
      </div>
    </AbsoluteFill>
  );
};
