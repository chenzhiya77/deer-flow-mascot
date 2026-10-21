import { AbsoluteFill, Img, staticFile } from "remotion";

import { BEAK_CANVAS, BEAK_ORDER } from "./beak-manifest";

export const Beak = () => {
  return (
    <AbsoluteFill>
      {BEAK_ORDER.map((name) => {
        const p = BEAK_CANVAS[name];
        return (
          <Img
            key={name}
            src={staticFile(`parts-user/${name}.png`)}
            style={{ position: "absolute", left: p.x, top: p.y, width: p.w, height: p.h }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
