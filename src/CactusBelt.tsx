import { AbsoluteFill, Img, staticFile } from "remotion";

import { BELT_ORDER, PARTS_BELT } from "./belt-manifest";

export const CactusBelt = () => {
  return (
    <AbsoluteFill>
      {BELT_ORDER.map((name) => {
        const p = PARTS_BELT[name];
        return (
          <Img
            key={name}
            src={staticFile(`parts-belt/${name}.png`)}
            style={{ position: "absolute", left: p.x, top: p.y, width: p.w, height: p.h }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
