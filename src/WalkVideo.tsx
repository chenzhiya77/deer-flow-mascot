import { useCurrentFrame } from "remotion";

import { RidingCut } from "./RidingCut";

const CYCLE = 30;
const FOOT_SWING = 6;

export const WalkVideo = () => {
  const frame = useCurrentFrame();
  const phase = (frame / CYCLE) * Math.PI * 2;
  const swing = Math.sin(phase);
  const footSwing = Math.sin(phase - 0.5); // 脚比身体慢半拍，垂摆更自然
  const nearSide = swing * 22;
  const farSide = -swing * 22;
  return (
    <RidingCut
      pose="ride"
      specs={{
        horse: {
          body: { ty: -Math.abs(swing) * 7, rot: swing * 1.2 },
          local: {
            leg_0: { rot: farSide, org: "50% 0%" },
            leg_1: { rot: nearSide, org: "50% 0%" },
            leg_2: { rot: nearSide, org: "50% 0%" },
            leg_3: { rot: farSide, org: "50% 0%" },
          },
          planted: [],
        },
        duck: {
          // 跷跷板：接触点（支点）固定不动，身体绕它左右摆
          body: { rot: swing * 3 },
          // 两只脚绕脚背顶端（连接点）垂摆、反相交替
          local: {
            boot_l: { rot: footSwing * FOOT_SWING, org: "50% 0%" },
            boot_r: { rot: -footSwing * FOOT_SWING, org: "50% 0%" },
          },
          planted: [],
        },
      }}
    />
  );
};
