import { AbsoluteFill, Img, staticFile } from "remotion";

import { BANDANA_ORDER, PARTS_BANDANA } from "./bandana-manifest";

export const Bandana = () => {
  return (
    <AbsoluteFill>
      {BANDANA_ORDER.map((name) => {
        const p = PARTS_BANDANA[name];
        return (
          <Img
            key={name}
            src={staticFile(`parts-bandana/${name}.png`)}
            style={{ position: "absolute", left: p.x, top: p.y, width: p.w, height: p.h }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
