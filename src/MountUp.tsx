import { AbsoluteFill, useCurrentFrame } from "remotion";

import { DuckRig, type DuckPoseSpec } from "./CowboyCutUser";
import { HorseRig, type HorsePoseSpec } from "./HorseCut";
import { SEAT } from "./seat-config";
import { solveSeatY } from "./seat-solver";

const SEAT_ANCHOR = "669px 1130px";
const BODY_MID = 812;

// 站位：鸭在马屁股后面（马尾侧，整鸭不压到马），马在右（站定）；鸭向前跃出弧线落上马背。
// 落点 = 求解器的座位解 ⇒ 正好贴鞍沿、防穿模。
const STAND_TX = -660;
const GROUND_TY = 63;
const LAND_TX = SEAT.tx;
const LAND_TY = solveSeatY(SEAT, {});
const APEX_TY = LAND_TY - 80; // 弧顶过冲 80px（够越过鞍桥即可，不必更高）
const DIST = LAND_TX - STAND_TX;

// ── 运动曲线：轨迹用解析曲线（速度连续，不在关键帧上急停）；形变只留蹲与极小落地缓冲。
const clamp01 = (t: number) => Math.max(0, Math.min(1, t));
const easeInOutCubic = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

const FLY_IN = 6; // 蓄力结束、起跳
const FLY_T = 30; // 飞行 30 帧（1 秒）——抛体节奏
const APEX_U = 0.75; // 弧顶相位：落点比起跳点高 637px、只比弧顶低 80px ⇒ 物理上弧顶自然偏后
const FLY_OUT = FLY_IN + FLY_T;

// 姿势（脚/翅膀/前倾）：少量关键帧 + 平滑插值；停点都落在自然停顿上（蹲、蹬出、收腿、落定）
type PoseKey = { f: number; rot: number; leg: number; arm: number };

const POSE: PoseKey[] = [
  { f: 0, rot: 0, leg: 0, arm: 0 },
  { f: 6, rot: -2, leg: -16, arm: 18 }, // 蹲：微后仰、脚收、翅压
  { f: 12, rot: 4, leg: 24, arm: -28 }, // 蹬出：脚后蹬、翅上带
  { f: 20, rot: 6, leg: -22, arm: -40 }, // 空中：收腿扬翅、前倾最大
  { f: 28, rot: 5, leg: -14, arm: -32 }, // 越过鞍桥
  { f: 36, rot: 1, leg: 12, arm: -6 }, // 落下：脚先探向马背
  { f: 44, rot: 0, leg: -6, arm: 12 }, // 落定回收
  { f: 54, rot: 0, leg: 0, arm: 0 }, // 坐定＝骑乘姿势
  { f: 90, rot: 0, leg: 0, arm: 0 },
];

const samplePose = (f: number): PoseKey => {
  for (let i = 0; i < POSE.length - 1; i++) {
    const a = POSE[i];
    const b = POSE[i + 1];
    if (f >= a.f && f <= b.f) {
      const t = (f - a.f) / (b.f - a.f);
      const e = t * t * (3 - 2 * t);
      return {
        f,
        rot: a.rot + (b.rot - a.rot) * e,
        leg: a.leg + (b.leg - a.leg) * e,
        arm: a.arm + (b.arm - a.arm) * e,
      };
    }
  }
  return POSE[POSE.length - 1];
};

// 取景缩放：整场景（鸭站位+马+地面）缩 0.55 居中，四周留白
const S = 0.55;
const BBOX = { x0: -361, y0: 55 };
const TARGET_X = (1856 - 1843 * S) / 2;
const TARGET_Y = 350;

export const MountUp = () => {
  const frame = useCurrentFrame();
  const pose = samplePose(frame);

  // 轨迹＝真抛体：水平匀速（抛体水平分量），竖直为重力抛物线（上升 easeOut、下落 easeIn，
  // 二者在弧顶速度同时过零 ⇒ 天然连续，无关键帧急停）
  const u = clamp01((frame - FLY_IN) / FLY_T);
  const tx = STAND_TX + DIST * u;
  const ty =
    frame < FLY_IN
      ? GROUND_TY
      : u < APEX_U
        ? GROUND_TY + (APEX_TY - GROUND_TY) * (1 - (1 - u / APEX_U) ** 2)
        : APEX_TY + (LAND_TY - APEX_TY) * ((u - APEX_U) / (1 - APEX_U)) ** 2;

  // 形变：只有蓄力蹲（0.94）与落地极小缓冲（0.985）；飞行段恒 1 ⇒ 形状不走样、末态=骑乘原样
  let sy = 1;
  if (frame < FLY_IN) {
    sy = 1 - 0.06 * easeInOutCubic(clamp01(frame / FLY_IN));
  } else if (frame >= FLY_OUT) {
    sy = 1 - 0.015 * Math.sin(Math.PI * clamp01((frame - FLY_OUT) / 12));
  }

  const horse: HorsePoseSpec = { body: {}, local: {}, detached: {}, planted: [] };

  const duck: DuckPoseSpec = {
    body: { rot: pose.rot, sy, sx: 1 / sy },
    local: {
      boot_l: { rot: pose.leg, org: "50% 0%" },
      boot_r: { rot: pose.leg * 0.85, org: "50% 0%" },
      hand_0: { rot: pose.arm, org: "50% 0%" },
      hand_1: { rot: pose.arm, org: "50% 0%" },
    },
    detached: {},
    planted: [],
  };

  const seatStyle: React.CSSProperties = {
    position: "absolute",
    inset: 0,
    transformOrigin: SEAT_ANCHOR,
    transform: `translate(${tx}px, ${ty}px) rotate(${SEAT.rot}deg) scale(${SEAT.sx * SEAT.s}, ${SEAT.s})`,
  };

  return (
    <AbsoluteFill style={{ backgroundColor: "#FFFFFF" }}>
      <div
        style={{
          position: "absolute",
          inset: 0,
          transformOrigin: "0 0",
          transform: `translate(${TARGET_X - BBOX.x0 * S}px, ${TARGET_Y - BBOX.y0 * S}px) scale(${S})`,
        }}
      >
        <svg viewBox="0 0 1856 1280" width="100%" height="100%" style={{ position: "absolute" }}>
          <ellipse cx={890} cy={1272} rx={580} ry={20} fill="#EFE6D2" />
        </svg>
        <HorseRig
          pose="rest"
          spec={horse}
          mountBack={
            <div style={seatStyle}>
              <DuckRig pose="rest" spec={duck} layer="far" splitAt={BODY_MID} />
            </div>
          }
          mount={
            <div style={seatStyle}>
              <DuckRig pose="rest" spec={duck} layer="near" splitAt={BODY_MID} />
            </div>
          }
        />
      </div>
    </AbsoluteFill>
  );
};
