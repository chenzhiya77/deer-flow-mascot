import { AbsoluteFill, useCurrentFrame } from "remotion";

import { DuckRig, type DuckPoseSpec } from "./CowboyCutUser";

const CYCLE = 30;

// 一个完整跳跃的关键帧（u∈[0,1]）：蹬地压缩 → 起跳伸展 → 腾空 → 下落 → 落地压缩 → 还原。
// ty 为负=上跳；sy<1=压扁、>1=拉长（sx 取倒数保体积）；leg/arm 为脚、翅膀的摆角。
type JumpKey = { u: number; ty: number; sy: number; leg: number; arm: number };

const KEYS: JumpKey[] = [
  { u: 0.0, ty: 0, sy: 1, leg: 0, arm: 0 },
  { u: 0.12, ty: 30, sy: 0.82, leg: -20, arm: 22 },
  { u: 0.22, ty: -50, sy: 1.12, leg: 25, arm: -32 },
  { u: 0.45, ty: -230, sy: 1.0, leg: -28, arm: -46 },
  { u: 0.68, ty: -50, sy: 1.08, leg: 18, arm: -12 },
  { u: 0.78, ty: 28, sy: 0.84, leg: -12, arm: 20 },
  { u: 1.0, ty: 0, sy: 1, leg: 0, arm: 0 },
];

const sample = (u: number): JumpKey => {
  for (let i = 0; i < KEYS.length - 1; i++) {
    const a = KEYS[i];
    const b = KEYS[i + 1];
    if (u >= a.u && u <= b.u) {
      const f = (u - a.u) / (b.u - a.u);
      const e = f * f * (3 - 2 * f);
      return {
        u,
        ty: a.ty + (b.ty - a.ty) * e,
        sy: a.sy + (b.sy - a.sy) * e,
        leg: a.leg + (b.leg - a.leg) * e,
        arm: a.arm + (b.arm - a.arm) * e,
      };
    }
  }
  return KEYS[KEYS.length - 1];
};

// 整鸭缩放取景（与 DuckWalk 同一取景）：切件并集 x -246..1114、y 37..1305
const S = 0.62;
const BBOX = { x0: -246, y0: 37 };
const TARGET_X = (1856 - 1360 * S) / 2;
const TARGET_Y = 360;

export const DuckJump = () => {
  const frame = useCurrentFrame();
  const k = sample((frame % CYCLE) / CYCLE);
  const spec: DuckPoseSpec = {
    body: { ty: k.ty, sy: k.sy, sx: 1 / k.sy },
    local: {
      boot_l: { rot: k.leg, org: "50% 0%" },
      boot_r: { rot: k.leg * 0.85, org: "50% 0%" },
      hand_0: { rot: k.arm, org: "50% 0%" },
      hand_1: { rot: k.arm, org: "50% 0%" },
    },
    detached: {},
    planted: [],
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
