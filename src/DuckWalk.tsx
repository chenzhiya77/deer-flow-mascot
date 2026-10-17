import { AbsoluteFill, useCurrentFrame } from "remotion";

import { DuckRig, type DuckPoseSpec } from "./CowboyCutUser";

export type Gait = "walk" | "run";

const GAITS: Record<
  Gait,
  { cycle: number; leg: number; bob: number; waddle: number; arm: number }
> = {
  walk: { cycle: 30, leg: 18, bob: 10, waddle: 2.5, arm: 6 },
  run: { cycle: 15, leg: 34, bob: 20, waddle: 4, arm: 18 },
};

// 整鸭缩放取景：切件并集（鸭坐标系）x -246..1114、y 37..1305，缩放后居中留白
const S = 0.62;
const BBOX = { x0: -246, y0: 37 };
const TARGET_X = (1856 - 1360 * S) / 2;
const TARGET_Y = 360;

export const DuckWalk = ({ gait = "walk" }: { readonly gait?: Gait }) => {
  const frame = useCurrentFrame();
  const cfg = GAITS[gait];
  const phase = (frame / cfg.cycle) * Math.PI * 2;
  const step = Math.sin(phase);
  const bob = -Math.abs(Math.sin(phase)) * cfg.bob;
  const spec: DuckPoseSpec = {
    // 一步一颠 + 小幅左右摇摆（鸭子标志性的摇摇摆摆），晃动轴仍是脚身连接点
    body: { ty: bob, rot: step * cfg.waddle },
    local: {
      boot_l: { rot: step * cfg.leg, org: "50% 0%" },
      boot_r: { rot: -step * cfg.leg, org: "50% 0%" },
      hand_0: { rot: -step * cfg.arm, org: "50% 0%" },
      hand_1: { rot: step * cfg.arm, org: "50% 0%" },
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
