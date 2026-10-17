import { AbsoluteFill } from "remotion";

import { DuckRig, duckBodyTf } from "./CowboyCutUser";
import { HorseRig } from "./HorseCut";
import { SEAT } from "./seat-config";
import { solveSeatY } from "./seat-solver";

export type RidePose = "rest" | "ride";

type Seat = {
  horse: "rest" | "step";
  duck: "rest" | "wave";
};

const SEAT_ANCHOR = "669px 1130px";

// 黄色方块（鸭身）外框边实测：切件坐标系 x 426..1198 → 中点 812。
// 注意基准是「身体方块」的一半，不是素材外框（素材含左伸的帽檐）。
// 切线按切件自身框换算、随切件平移一起走 ⇒ 始终落在方块中线上（即支点所在列）。
const BODY_MID = 812;

const POSES: Record<RidePose, Seat> = {
  rest: { horse: "rest", duck: "rest" },
  ride: { horse: "step", duck: "wave" },
};

export const RidingCut = ({
  pose,
  specs,
  markAnchor = false,
}: {
  readonly pose: RidePose;
  readonly markAnchor?: boolean;
  readonly specs?: {
    horse: import("./HorseCut").HorsePoseSpec;
    duck: import("./CowboyCutUser").DuckPoseSpec;
  };
}) => {
  const cfg = POSES[pose];
  const duckBody = specs?.duck.body ?? duckBodyTf(cfg.duck);
  const ty = solveSeatY(SEAT, duckBody);
  const seatStyle: React.CSSProperties = {
    position: "absolute",
    inset: 0,
    transformOrigin: SEAT_ANCHOR,
    transform: `translate(${SEAT.tx}px, ${ty}px) rotate(${SEAT.rot}deg) scale(${SEAT.sx * SEAT.s}, ${SEAT.s})`,
  };
  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#FFFFFF"
      }}
    >
      <svg viewBox="0 0 1856 1280" width="100%" height="100%" style={{ position: "absolute" }}>
        <ellipse cx={890} cy={1272} rx={580} ry={20} fill="#EFE6D2" />
      </svg>
      <HorseRig
        pose={cfg.horse}
        spec={specs?.horse}
        mountBack={
          <div style={seatStyle}>
            <DuckRig pose={cfg.duck} spec={specs?.duck} layer="far" splitAt={BODY_MID} />
          </div>
        }
        mount={
          <div style={seatStyle}>
            <DuckRig
              pose={cfg.duck}
              spec={specs?.duck}
              layer="near"
              splitAt={BODY_MID}
              markAnchor={markAnchor}
            />
          </div>
        }
      />
    </AbsoluteFill>
  );
};
