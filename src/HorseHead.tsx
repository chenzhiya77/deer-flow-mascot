import type { CSSProperties } from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";

import {
  HORSE_EYE_STATES,
  HORSE_HEAD_BASE_ORDER,
  PARTS_HORSE_HEAD,
  type HorseEyeState,
} from "./horse-head-manifest";

export type HorseHeadProps = {
  eye?: HorseEyeState;
  hair?: boolean;
};

export const HorseHead = ({ eye = "normal", hair = true }: HorseHeadProps) => {
  const hairPart = PARTS_HORSE_HEAD.hair;
  const frontEar = PARTS_HORSE_HEAD.ear_front;
  const earRight = frontEar.x + frontEar.w - hairPart.x;
  const earBottom = frontEar.y + frontEar.h - hairPart.y;
  const hairStyle: CSSProperties = {
    clipPath: `polygon(${earRight}px 0, 100% 0, 100% 100%, 0 100%, 0 ${earBottom}px, ${earRight}px ${earBottom}px)`,
  };

  const order = [
    ...HORSE_HEAD_BASE_ORDER,
    ...(hair ? ["hair"] : []),
    HORSE_EYE_STATES[eye],
  ];

  return (
    <AbsoluteFill>
      {order.map((name) => {
        const p = PARTS_HORSE_HEAD[name];
        return (
          <Img
            key={name}
            src={staticFile(`parts-horse/${name}.png`)}
            style={{
              position: "absolute",
              left: p.x,
              top: p.y,
              width: p.w,
              height: p.h,
              ...(name === "hair" ? hairStyle : {}),
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
