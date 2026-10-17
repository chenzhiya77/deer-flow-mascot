import { solveSeatY } from "./seat-solver";

export type SeatConfig = {
  tx: number;
  rot: number;
  sx: number;
  s: number;
};

// ty 不再手填：由稳定点规则实时求解（见 seat-solver.ts）——
// 鸭方块底边 × 身体垂直划分线的交点（切件平移后 472.9,1160.3）永远停在马的图片之外，故不会穿模。
export const SEAT: SeatConfig = {
  tx: 130,
  rot: 0,
  sx: 0.9,
  s: 0.45,
};

export const SEAT_TY = solveSeatY(SEAT);
