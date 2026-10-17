import { AbsoluteFill, useCurrentFrame } from "remotion";

import { DuckRig, type DuckPoseSpec } from "./CowboyCutUser";
import type { EyeState } from "./eye-states-manifest";

// 取景与 DuckWalk 同一套（0.62 定式），保证四段鸭片同景别
const S = 0.62;
const BBOX = { x0: -246, y0: 37 };
const TARGET_X = (1856 - 1360 * S) / 2;
const TARGET_Y = 360;

// —— 动作时间线（动作帧 f = 原始帧 - shift，30fps）——
// f0        中性站定
// f12–20    蓄力：手先下沉后拉（anticipation）
// f20–38    上抬到头侧（带过冲回落）
// f36–60    挠 1：3 下 × 8f
// f60–68    停（"嗯……"微沉）
// f68–86    挠 2：3 下 × 6f（节奏加快，动作不机械）
// f86–96    停＋眨眼
// f96–116   收手回落（缓入缓出＋轻微回弹）
// f116–120  站定收尾
// 眼睛编排走 steps（按原始帧）：V2（shift=72）＝[[0,normal],[12,wuyu],[48,zhuangsha],[182,normal]]：正常 0.4s→无语 1.2s→装傻 1.2s→挠头→回正常
const SCRATCH = { tx: 152, ty: -387, org: "50% 0%" };
const BURSTS: ReadonlyArray<readonly [number, number, number]> = [
  [36, 60, 8],
  [68, 86, 6],
];
const RUB_TY = 7;
const RUB_TX = 2.5;
const RUB_ROT = 4;

type Key = readonly [number, number];

const kf = (f: number, keys: readonly Key[]): number => {
  if (f <= keys[0][0]) return keys[0][1];
  for (let i = 0; i < keys.length - 1; i++) {
    const [f0, v0] = keys[i];
    const [f1, v1] = keys[i + 1];
    if (f <= f1) {
      const t = (f - f0) / (f1 - f0);
      return v0 + (v1 - v0) * (t * t * (3 - 2 * t));
    }
  }
  return keys[keys.length - 1][1];
};

// 搓动：在 burst 窗口内取相位，整数周期 ⇒ 窗口两端速度自然归零、无跳变
const rubPhase = (f: number): number => {
  for (const [a, b, cycle] of BURSTS) {
    if (f >= a && f <= b) return ((f - a) / cycle) * Math.PI * 2;
  }
  return 0;
};

const DEFAULT_STEPS: ReadonlyArray<readonly [number, EyeState]> = [[0, "normal"]];

export const ThinkScratch = ({
  steps,
  shift = 0,
}: {
  readonly steps?: ReadonlyArray<readonly [number, EyeState]>;
  readonly shift?: number;
}) => {
  const raw = useCurrentFrame();
  const f = raw - shift;
  const p = rubPhase(f);
  const rub = Math.sin(p);

  // 手：蓄力 → 过冲上抬 → 搓动 → 回落回弹
  const baseTx = kf(f, [
    [0, 0],
    [12, 0],
    [20, -14],
    [32, SCRATCH.tx + 10],
    [38, SCRATCH.tx],
    [96, SCRATCH.tx],
    [108, -8],
    [116, 0],
    [120, 0],
  ]);
  const baseTy = kf(f, [
    [0, 0],
    [12, 0],
    [20, 26],
    [32, SCRATCH.ty - 14],
    [38, SCRATCH.ty],
    [96, SCRATCH.ty],
    [108, 8],
    [116, 0],
    [120, 0],
  ]);
  const hand = {
    tx: baseTx + rub * RUB_TX,
    ty: baseTy + rub * RUB_TY,
    rot: rub * RUB_ROT,
    org: SCRATCH.org,
  };

  // 身体：呼吸 + 靠向挠头侧 + 搓动反向微推（跷跷板轴仍为脚身链接线中点）
  const lean = kf(f, [
    [0, 0],
    [10, 0],
    [24, -2],
    [60, -2],
    [68, -2.2],
    [86, -2.2],
    [92, -2.8],
    [98, -2.8],
    [112, 0.4],
    [120, 0],
  ]);
  const breathe = Math.sin((f / 75) * Math.PI * 2) * 2.2;
  const body = {
    ty: breathe - rub * 1.4,
    rot: lean + rub * 0.4,
  };

  // 眼睛编排：steps=[起始帧,状态]，换件发生在眨眼闭合帧（压 sy=0.02 藏宽/窄眼跳变）
  const seq = steps ?? DEFAULT_STEPS;
  let eyes: EyeState = seq[0][1];
  for (const [sf, s] of seq) if (raw >= sf) eyes = s;
  const swapBlink = (c: number) => {
    const d = Math.abs(raw - c);
    return d <= 1 ? 0.02 : d === 2 ? 0.45 : 1;
  };
  let blink = f >= 92 && f <= 94 ? 0.12 : 1;
  for (const [sf] of seq.slice(1)) blink = Math.min(blink, swapBlink(sf));

  const spec: DuckPoseSpec = {
    body,
    local: {
      eye_0: { sy: blink },
      eye_1: { sy: blink },
      hand_0: hand,
      hand_1: { rot: -lean * 0.6, org: "50% 0%" },
    },
    planted: ["boot_l", "boot_r"],
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
        <DuckRig pose="rest" spec={spec} eyes={eyes} />
      </div>
    </AbsoluteFill>
  );
};
