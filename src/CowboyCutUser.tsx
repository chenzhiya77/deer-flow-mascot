import { AbsoluteFill, Img, staticFile } from "remotion";

import { EYE_SWAP, PARTS_EYES, type EyeState } from "./eye-states-manifest";
import { PARTS_USER } from "./parts-user-manifest";
import { PART_OFFSET, SEAT_ANCHOR_PT } from "./seat-solver";

const PARTS_ALL = { ...PARTS_USER, ...PARTS_EYES };

export type UserPose = "rest" | "wave" | "blink";

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
}: {
  readonly pose: UserPose;
  readonly layer?: "all" | "near" | "far";
  readonly splitAt?: number;
  readonly spec?: DuckPoseSpec;
  readonly eyes?: EyeState;
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
          const part = <Part name={rname} tf={spec.local[name]} clip={clip} />;
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

export const CowboyCutUser = ({
  pose,
  eyes = "normal",
}: {
  readonly pose: UserPose;
  readonly eyes?: EyeState;
}) => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#FFFFFF" }}>
      <DuckRig pose={pose} eyes={eyes} />
    </AbsoluteFill>
  );
};

export const duckBodyTf = (pose: UserPose): { tx?: number; ty?: number; rot?: number } =>
  POSES[pose].body;
