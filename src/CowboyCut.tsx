import { AbsoluteFill, Img, staticFile } from "remotion";

import { PARTS } from "./parts-manifest";

export type PoseName = "rest" | "wave" | "blink";

type PartTransform = {
  tx?: number;
  ty?: number;
  rot?: number;
  sx?: number;
  sy?: number;
  ox?: number;
  oy?: number;
};

const ORDER = [
  "boot_l",
  "boot_r",
  "body",
  "bolt",
  "hat",
  "eye_l",
  "eye_r",
  "beak",
  "hand_l",
  "hand_r",
] as const;

const POSES: Record<PoseName, Partial<Record<string, PartTransform>>> = {
  rest: {},
  wave: {
    body: { rot: -2, ox: 0.5, oy: 1 },
    hat: { tx: -8, ty: -10, rot: -4, ox: 0.5, oy: 1 },
    hand_r: { tx: -40, ty: -240, rot: -20, ox: 0.5, oy: 0 },
    boot_l: { rot: -10, ox: 0.5, oy: 0 },
  },
  blink: {
    eye_l: { sy: 0.12, ox: 0.5, oy: 0.5 },
    eye_r: { sy: 0.12, ox: 0.5, oy: 0.5 },
    hat: { ty: 4, ox: 0.5, oy: 1 },
    bolt: { rot: 5, ox: 0.2, oy: 0.9 },
  },
};

export const CowboyCut = ({ pose }: { readonly pose: PoseName }) => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#FFFFFF" }}>
      {ORDER.map((name) => {
        const p = PARTS[name];
        const t = POSES[pose][name] ?? {};
        const transforms: string[] = [];
        if (t.tx || t.ty) transforms.push(`translate(${t.tx ?? 0}px, ${t.ty ?? 0}px)`);
        if (t.rot) transforms.push(`rotate(${t.rot}deg)`);
        if (t.sx || t.sy) transforms.push(`scale(${t.sx ?? 1}, ${t.sy ?? 1})`);
        return (
          <Img
            key={name}
            src={staticFile(`parts/${p.file}`)}
            style={{
              position: "absolute",
              left: p.x,
              top: p.y,
              width: p.w,
              height: p.h,
              transformOrigin: `${(t.ox ?? 0) * p.w}px ${(t.oy ?? 0) * p.h}px`,
              transform: transforms.length > 0 ? transforms.join(" ") : undefined,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
