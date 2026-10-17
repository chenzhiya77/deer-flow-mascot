import { AbsoluteFill, Img, staticFile } from "remotion";

import { PARTS_HORSE } from "./horse-manifest";
import { HORSE_PART_OFFSET } from "./horse-topline";

export type HorsePose = "rest" | "step";

type Tf = {
  tx?: number;
  ty?: number;
  rot?: number;
  sx?: number;
  sy?: number;
  org?: string;
};

const BODY_ANCHOR = "949px 1012px";

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

export type HorsePoseSpec = {
  body: Tf;
  local: Partial<Record<string, Tf>>;
  detached: Partial<Record<string, Tf>>;
  planted: string[];
};

const POSES: Record<HorsePose, HorsePoseSpec> = {
  rest: { body: {}, local: {}, detached: {}, planted: [] },
  step: {
    body: { ty: -8, rot: -1 },
    local: {
      leg_2: { rot: 16, org: "50% 0%" },
      leg_0: { rot: -8, org: "50% 0%" },
    },
    detached: {},
    planted: ["leg_3"],
  },
};

const ATTACHED = ["leg_0", "leg_1", "leg_2", "leg_3", "body"] as const;

const Part = ({ name, tf }: { readonly name: string; readonly tf?: Tf }) => {
  const p = PARTS_HORSE[name];
  return (
    <Img
      src={staticFile(`parts-horse/${name}.png`)}
      style={{
        position: "absolute",
        left: p.x,
        top: p.y,
        width: p.w,
        height: p.h,
        transformOrigin: tf?.org ?? "50% 50%",
        transform: tfString(tf),
        translate: `${HORSE_PART_OFFSET.x}px ${HORSE_PART_OFFSET.y}px`
      }}
    />
  );
};

export const HorseRig = ({
  pose,
  mountBack,
  mount,
  spec: specProp,
}: {
  readonly pose: HorsePose;
  readonly mountBack?: React.ReactNode;
  readonly mount?: React.ReactNode;
  readonly spec?: HorsePoseSpec;
}) => {
  const spec = specProp ?? POSES[pose];
  const detached = new Set(Object.keys(spec.detached));
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
        {ATTACHED.filter((name) => name !== "body" && !detached.has(name)).map((name) =>
          spec.planted.includes(name) ? (
            <div
              key={name}
              style={{
                position: "absolute",
                inset: 0,
                transformOrigin: BODY_ANCHOR,
                transform: inverseTf(spec.body),
              }}
            >
              <Part name={name} tf={spec.local[name]} />
            </div>
          ) : (
            <Part key={name} name={name} tf={spec.local[name]} />
          ),
        )}
        {mountBack}
        <Part name="body" tf={spec.local["body"]} />
        {mount}
      </div>
      {[...detached].map((name) => (
        <Part key={`detached-${name}`} name={name} tf={spec.detached[name]} />
      ))}
    </>
  );
};

export const HorseCut = ({
  pose,
  mountBack,
  mount,
}: {
  readonly pose: HorsePose;
  readonly mountBack?: React.ReactNode;
  readonly mount?: React.ReactNode;
}) => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#FFFFFF" }}>
      <HorseRig pose={pose} mountBack={mountBack} mount={mount} />
    </AbsoluteFill>
  );
};
