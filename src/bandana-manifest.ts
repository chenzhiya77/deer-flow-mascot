// 独立方巾装配表：坐标落在参考图 Hya-fangjin-cankao.png 的 2120×724 画布上。
// 分层（动画用）：带身（diceng，可动）→ 垂尾（tuowei，可动）→ 结扣（jiekou，静止锚点，压最上）。
// 带身件与参考同画布 1:1，原位 (0,0)（可见像素 97.7% ≤12 色差）。
// 结扣 / 垂尾与旧 shangceng 同画布 539×1055（重拆后合成 99.1% ≤12），沿用 0.4875
// → 两件同为 (263,208) 263×514（与参考平均色差 8.3 / 13.5）。
// 注：file 仅记录原素材文件名（溯源），运行时按 key 拼 parts-bandana/<key>.png，不读此字段。
import type { PartDef } from "./horse-manifest";

export const BANDANA_W = 2120;
export const BANDANA_H = 724;

export const PARTS_BANDANA: Record<string, PartDef> = {
  band: { file: "Hya-fangjin-diceng.png", x: 0, y: 0, w: 2120, h: 724 },
  tail: { file: "Hya-fangjin-tuowei.png", x: 263, y: 208, w: 263, h: 514 },
  knot: { file: "Hya-fangjin-jiekou.png", x: 263, y: 208, w: 263, h: 514 },
};

export const BANDANA_ORDER = ["band", "tail", "knot"] as const;

// 戴到鸭身上：参考图 Hya-fangjin-zhengti.png 的鸭子相对切件空间平移 (+127,+4.5)（眼睛实测），
// 方巾整张画布按 0.38 放在鸭子空间的 (407,670.5)（红区 IoU 0.495，带身横跨胸前与参考同位）。
// 参考图是 AI 着妆版，结/垂尾的姿态与素材不同，此处以带身跨度对齐为准。
export const BANDANA_ON_DUCK = { x: 407, y: 670.5, s: 0.38 };
