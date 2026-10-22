import { AbsoluteFill, Img, staticFile } from "remotion";

import {
  HORSE_EYE_STATES,
  HORSE_HEAD_BASE_ORDER,
  PARTS_HORSE_HEAD,
  type HorseEyeState,
} from "./horse-head-manifest";

export type HorseHeadProps = {
  eye?: HorseEyeState;
};

export const HorseHead = ({ eye = "normal" }: HorseHeadProps) => {
  const order = [...HORSE_HEAD_BASE_ORDER, HORSE_EYE_STATES[eye]];
  return (
    <AbsoluteFill>
      {order.map((name) => {
        const p = PARTS_HORSE_HEAD[name];
        return (
          <Img
            key={name}
            src={staticFile(`parts-horse/${name}.png`)}
            style={{ position: "absolute", left: p.x, top: p.y, width: p.w, height: p.h }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
