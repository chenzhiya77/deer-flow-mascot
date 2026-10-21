import { AbsoluteFill, Img, staticFile } from "remotion";

import { Bandana } from "./Bandana";
import { BANDANA_H, BANDANA_ON_DUCK, BANDANA_W } from "./bandana-manifest";
import { AHOGE_CLIP, PARTS_AHOGE } from "./ahoge-manifest";
import { BEAK_ORDER, PARTS_BEAK } from "./beak-manifest";
import { CactusBelt } from "./CactusBelt";
import { BELT_H, BELT_ON_DUCK, BELT_W } from "./belt-manifest";
import { EYE_SWAP, PARTS_EYES, type EyeState } from "./eye-states-manifest";
import { PARTS_USER, type PartDef } from "./parts-user-manifest";
import { PART_OFFSET, SEAT_ANCHOR_PT } from "./seat-solver";

const PARTS_ALL: Record<string, PartDef> = { ...PARTS_USER, ...PARTS_EYES, ...PARTS_BEAK, ...PARTS_AHOGE };

export type UserPose = "rest" | "wave" | "blink";
export type DuckBelt = "normal" | "cactus";
export type DuckMouth = "normal" | "split";

type Tf = {
  tx?: number;
  ty?: number;
  rot?: number;
  sx?: number;
  sy?: number;
  org?: string;
};

const BODY_ANCHOR = `${SEAT_ANCHOR_PT.x}px ${SEAT_ANCHOR_PT.y}px`;

const tfString = (t: Tf | undefined): string | undefined => {
  if (!t) return undefined;
  const parts: string[] = [];
  if (t.tx || t.ty) parts.push(`translate(${t.tx ?? 0}px, ${t.ty ?? 0}px)`);
  if (t.rot) parts.push(`rotate(${t.rot}deg)`);
  if (t.sx || t.sy) parts.push(`scale(${t.sx ?? 1}, ${t.sy ?? 1})`);
  return parts.length > 0 ? parts.join(" ") : undefined;
};

const inverseTf = (t: Tf | undefined): string | undefined => {
  if (!t) return undefined;
  const parts: string[] = [];
  if (t.sx || t.sy) parts.push(`scale(${1 / (t.sx ?? 1)}, ${1 / (t.sy ?? 1)})`);
  if (t.rot) parts.push(`rotate(${-t.rot}deg)`);
  if (t.tx || t.ty) parts.push(`translate(${-(t.tx ?? 0)}px, ${-(t.ty ?? 0)}px)`);
  return parts.length > 0 ? parts.join(" ") : undefined;
};

export type DuckPoseSpec = {
  body: Tf;
  local: Partial<Record<string, Tf>>;
  planted: string[];
};

const POSES: Record<UserPose, DuckPoseSpec> = {
  rest: { body: {}, local: {}, planted: [] },
  wave: {
    body: { rot: -2 },
    local: { hand_1: { tx: -30, ty: -240, rot: -20, org: "50% 0%" } },
    planted: [],
  },
  blink: {
    body: {},
    local: { eye_0: { sy: 0.12 }, eye_1: { sy: 0.12 } },
    planted: [],
  },
};

const ATTACHED = [
  "boot_l",
  "boot_r",
  "body",
  "ahoge",
  "belt",
  "eye_0",
  "eye_1",
  "beak",
  "hand_0",
  "hand_1",
] as const;

const Part = ({
  name,
  tf,
  clip,
}: {
  readonly name: string;
  readonly tf?: Tf;
  readonly clip?: string;
}) => {
  const p = PARTS_ALL[name];
  return (
    <Img
      src={staticFile(`parts-user/${name}.png`)}
      style={{
        position: "absolute",
        left: p.x,
        top: p.y,
        width: p.w,
        height: p.h,
        transformOrigin: tf?.org ?? "50% 50%",
        transform: tfString(tf),
        clipPath: clip,
        translate: `${PART_OFFSET.x}px ${PART_OFFSET.y}px`
      }}
    />
  );
};

const FAR_SIDE = new Set(["hand_1", "boot_r"]);
const SPLIT_PARTS = new Set(["body", "belt", "eye_0", "eye_1", "beak"]);

const CactusBeltOnDuck = () => (
  <div
    style={{
      position: "absolute",
      left: BELT_ON_DUCK.x + PART_OFFSET.x,
      top: BELT_ON_DUCK.y + PART_OFFSET.y,
      width: BELT_W,
      height: BELT_H,
      transform: `scale(${BELT_ON_DUCK.s})`,
      transformOrigin: "0 0",
    }}
  >
    <CactusBelt />
  </div>
);

const BandanaOnDuck = () => (
  <div
    style={{
      position: "absolute",
      left: BANDANA_ON_DUCK.x + PART_OFFSET.x,
      top: BANDANA_ON_DUCK.y + PART_OFFSET.y,
      width: BANDANA_W,
      height: BANDANA_H,
      transform: `scale(${BANDANA_ON_DUCK.s})`,
      transformOrigin: "0 0",
    }}
  >
    <Bandana />
  </div>
);

const partClip = (
  p: { x: number; w: number; h: number },
  splitAt: number,
  side: "near" | "far",
): string | undefined => {
  const lx = splitAt - p.x;
  // 两半各让 16px（32px 重叠）：羽化边深埋进对半内部 ⇒ 旋转/缩放下也不透缝
  if (side === "near") {
    if (lx <= 0 || lx >= p.w) return undefined;
    return `polygon(0px 0px, ${lx + 16}px 0px, ${lx + 16}px ${p.h}px, 0px ${p.h}px)`;
  }
  if (lx <= 0 || lx >= p.w) return undefined;
  return `polygon(${lx - 16}px 0px, ${p.w}px 0px, ${p.w}px ${p.h}px, ${lx - 16}px ${p.h}px)`;
};

export const DuckRig = ({
  pose,
  layer = "all",
  splitAt,
  spec: specProp,
  eyes = "normal",
  belt = "normal",
  bandana = false,
  mouth = "normal",
}: {
  readonly pose: UserPose;
  readonly layer?: "all" | "near" | "far";
  readonly splitAt?: number;
  readonly spec?: DuckPoseSpec;
  readonly eyes?: EyeState;
  readonly belt?: DuckBelt;
  readonly bandana?: boolean;
  readonly mouth?: DuckMouth;
}) => {
  const spec = specProp ?? POSES[pose];
  const swap = EYE_SWAP[eyes];
  const resolve = (name: string) => swap[name] ?? name;
  const names = ATTACHED.filter((name) => {
    if (layer === "all") return true;
    const isSplit = SPLIT_PARTS.has(name);
    if (splitAt !== undefined && isSplit) {
      const p = PARTS_ALL[resolve(name)];
      const lx = splitAt - p.x;
      return layer === "far" ? lx < p.w : lx > 0;
    }
    return layer === "far" ? FAR_SIDE.has(name) : !FAR_SIDE.has(name);
  });
  return (
    <>
      <div
        style={{
          position: "absolute",
          inset: 0,
          transformOrigin: BODY_ANCHOR,
          transform: tfString(spec.body),
        }}
      >
        {names.map((name) => {
          const rname = resolve(name);
          const p = PARTS_ALL[rname];
          const clip =
            splitAt !== undefined && SPLIT_PARTS.has(name)
              ? partClip(p, splitAt, layer === "far" ? "far" : "near")
              : undefined;
          const part = (
            <>
              {mouth === "split" && name === "beak" ? (
                BEAK_ORDER.map((bname) => (
                  <Part key={bname} name={bname} tf={spec.local[name]} clip={clip} />
                ))
              ) : belt === "cactus" && name === "belt" ? (
                <CactusBeltOnDuck />
              ) : (
                <Part
                  name={rname}
                  tf={spec.local[name]}
                  clip={name === "ahoge" ? AHOGE_CLIP : clip}
                />
              )}
              {bandana && name === "belt" ? <BandanaOnDuck /> : null}
            </>
          );
          return spec.planted.includes(name) ? (
            <div
              key={name}
              style={{
                position: "absolute",
                inset: 0,
                transformOrigin: BODY_ANCHOR,
                transform: inverseTf(spec.body),
              }}
            >
              {part}
            </div>
          ) : (
            <div key={name}>{part}</div>
          );
        })}
      </div>
    </>
  );
};

// 静帧构图：切件空间 → 画幅。参考图 Hya-fangjin-zhengti 的鸭位为 part+(127,4.5)（眼睛实测），
// 补回骑乘用 PART_OFFSET 导致的左裁（左手与帽檐出画）。
const STILL_TF = { x: 127 - PART_OFFSET.x, y: 4.5 - PART_OFFSET.y };

export const CowboyCutUser = ({
  pose,
  eyes = "normal",
  belt = "normal",
  bandana = false,
  mouth = "normal",
  background = "#FFFFFF",
}: {
  readonly pose: UserPose;
  readonly eyes?: EyeState;
  readonly belt?: DuckBelt;
  readonly bandana?: boolean;
  readonly mouth?: DuckMouth;
  readonly background?: string;
}) => {
  return (
    <AbsoluteFill style={{ backgroundColor: background }}>
      <div style={{ position: "absolute", inset: 0, transform: `translate(${STILL_TF.x}px, ${STILL_TF.y}px)` }}>
        <DuckRig pose={pose} eyes={eyes} belt={belt} bandana={bandana} mouth={mouth} />
      </div>
    </AbsoluteFill>
  );
};

export const duckBodyTf = (pose: UserPose): { tx?: number; ty?: number; rot?: number } =>
  POSES[pose].body;
