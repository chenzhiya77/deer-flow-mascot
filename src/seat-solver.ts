import { HORSE_ORIGIN, HORSE_TOPLINE } from "./horse-topline";

export type SeatTransform = {
  tx: number;
  rot: number;
  sx: number;
  s: number;
};

export type BodyTransform = {
  tx?: number;
  ty?: number;
  rot?: number;
};

// 切件统一平移（用户手调"接触点靠右"，落在 Part 的 translate 上，2026-10-14）。
// 支点/标记必须跟它对齐，否则标记跑到鸭身右边、晃动轴心也偏离鸭身。
export const PART_OFFSET = { x: -339.1, y: 33.3 };

// 稳定点：鸭子身体的底＝「脚与身体链接的那条线」（皮带下方）的中点，
// 在素材 0.hye-Zhengti.png 上实测：缝线 y 1125..1131、x 425..1199 → 中点 (812,1128)。
// 该点与鸭子绑定、跟着鸭子动（含切件平移）；且不得与马的图片重合 ⇒ 鸭永远不会穿模。
// 求解时把鸭自身姿势的身体变换一并算入（如 wave 的 rot:-2 会把锚点压低几像素）。
export const SEAT_ANCHOR_PT = { x: 812 + PART_OFFSET.x, y: 1128 + PART_OFFSET.y };

export const DUCK_ANCHOR = { x: 669, y: 1130 };

export function solveSeatY(seat: SeatTransform, body: BodyTransform = {}): number {
  // 鸭的身体变换以接触点为轴（DuckRig 的 transformOrigin = SEAT_ANCHOR_PT）⇒
  // 旋转不移动锚点，只有平移分量参与求解。
  const bx = SEAT_ANCHOR_PT.x + (body.tx ?? 0);
  const by = SEAT_ANCHOR_PT.y + (body.ty ?? 0);

  const rad = (seat.rot * Math.PI) / 180;
  const vx = bx - DUCK_ANCHOR.x;
  const vy = by - DUCK_ANCHOR.y;
  const sxs = vx * seat.sx * seat.s;
  const sys = vy * seat.s;
  const rx = sxs * Math.cos(rad) - sys * Math.sin(rad);
  const ry = sxs * Math.sin(rad) + sys * Math.cos(rad);
  const anchorX = DUCK_ANCHOR.x + rx + seat.tx;
  const anchorYFromTy = DUCK_ANCHOR.y + ry;
  const col = Math.round(anchorX - HORSE_ORIGIN.x);
  const clamped = Math.max(0, Math.min(HORSE_TOPLINE.length - 1, col));
  const top = HORSE_TOPLINE[clamped];
  // 鸭子和马的交接点：支点落在马背上沿、鸭底压进鞍沿 2px。
  // 6px 安全缝 ⇒ 鞍座凹处透白（已裁掉）；贴合 0px 仍剩发丝缝 ⇒ 压进鞍沿 4px 咬合（2026-10-14 他两轮调）。
  const toplineStageY = top < 0 ? 0 : top + HORSE_ORIGIN.y;
  return toplineStageY + 4 - anchorYFromTy;
}
