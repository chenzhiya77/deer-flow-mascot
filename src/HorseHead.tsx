import { AbsoluteFill, Img, staticFile } from "remotion";

import { HORSE_HEAD_ORDER, PARTS_HORSE_HEAD } from "./horse-head-manifest";

export const HorseHead = () => {
  return (
    <AbsoluteFill>
      {HORSE_HEAD_ORDER.map((name) => {
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
