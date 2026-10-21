// 独立仙人掌皮带装配表：坐标落在参考图 Hya-皮带-参考.png 的 760×181 画布上。
// 分层：带身 → 扣子（仙人掌扣压在带身上）。
// 带身件 1313×109 按 0.472 缩放 → (50,71) 620×51（带身棕色带实测对齐，扣子区不计入，形色 IoU 0.654）。
// 扣子件 674×572 按 0.1972 缩放 → (308,28) 133×113（仙人掌绿 84×96 ↔ 件 425×488，两轴同尺度）。
// 注：file 仅记录原素材文件名（溯源），运行时按 key 拼 parts-belt/<key>.png，不读此字段。
import type { PartDef } from "./horse-manifest";

export const BELT_W = 760;
export const BELT_H = 181;

export const PARTS_BELT: Record<string, PartDef> = {
  strap: { file: "Hya-pidai.png", x: 50, y: 71, w: 620, h: 51 },
  buckle: { file: "Hya-pidaikou.png", x: 308, y: 28, w: 133, h: 113 },
};

export const BELT_ORDER = ["strap", "buckle"] as const;

// 戴到鸭身上：整张参考画布按 1.25 放大后落在 duck-space。
// 带身棕带（参考 620×51 中的 610×42 @ 55.2,76.7）→ 旧皮带 belt.png 的棕带 (432,951,761×49)；
// 换算后扣框中心 (830.75,979.7) 与旧扣中心 (830.5,980) 重合。
export const BELT_ON_DUCK = { x: 363, y: 855.2, s: 1.25 };
