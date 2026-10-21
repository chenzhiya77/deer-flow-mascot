// 上下嘴定位表。整嘴参考 = public/parts-user/beak.png（1052×399，DuckRig 显示为 371×140 @ 655,603）。
// 上嘴按参考嘴外轮廓拟合：1307→1052 宽（左右不变），纵向压到 391→310、下移 12px
// （顶弧 / 分缝 / 鼻孔与整嘴对齐），露出下喙；
// 下嘴按黑描边轮廓拟合：s=0.69，画布 1065×208 @ (-7,201)，线宽 17–18px 与整嘴参考的 18–20px 对齐。
import type { PartDef } from "./parts-user-manifest";

export const BEAK_W = 1052;
export const BEAK_H = 399;

// 参考画布（整嘴件坐标系）里的落位；上嘴顶部超出画布 2px。
const CANVAS_RECTS = {
  beak_lower: { x: -7, y: 201, w: 1544 * 0.69, h: 302 * 0.69 },
  beak_upper: { x: 0, y: 2, w: 1052, h: 310 },
} as const;

export const BEAK_ON_DUCK = { x: 655, y: 603, w: 371, h: 140 };
const SX = BEAK_ON_DUCK.w / BEAK_W;
const SY = BEAK_ON_DUCK.h / BEAK_H;

export const PARTS_BEAK: Record<keyof typeof CANVAS_RECTS, PartDef> = {
  beak_lower: {
    file: "Hya-zui-xiahui_fuben.png",
    x: BEAK_ON_DUCK.x + CANVAS_RECTS.beak_lower.x * SX,
    y: BEAK_ON_DUCK.y + CANVAS_RECTS.beak_lower.y * SY,
    w: CANVAS_RECTS.beak_lower.w * SX,
    h: CANVAS_RECTS.beak_lower.h * SY,
  },
  beak_upper: {
    file: "Hya-zui-shanghui_fuben.png",
    x: BEAK_ON_DUCK.x + CANVAS_RECTS.beak_upper.x * SX,
    y: BEAK_ON_DUCK.y + CANVAS_RECTS.beak_upper.y * SY,
    w: CANVAS_RECTS.beak_upper.w * SX,
    h: CANVAS_RECTS.beak_upper.h * SY,
  },
};

export const BEAK_ORDER = ["beak_lower", "beak_upper"] as const;

// 独立静帧画布：上面留 16px 给上嘴超出参考画布的部分。
export const BEAK_PAD = 16;
export const BEAK_STILL_W = BEAK_W;
export const BEAK_STILL_H = BEAK_H + BEAK_PAD;
export const BEAK_CANVAS = {
  beak_lower: { ...CANVAS_RECTS.beak_lower, y: CANVAS_RECTS.beak_lower.y + BEAK_PAD },
  beak_upper: { ...CANVAS_RECTS.beak_upper, y: CANVAS_RECTS.beak_upper.y + BEAK_PAD },
} as const;
