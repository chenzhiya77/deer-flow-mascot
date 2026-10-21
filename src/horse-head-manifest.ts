// 独立马头装配表：坐标全部落在参考图 ma-tou.png 的 320×431 画布上，不挂在马身上。
// 分层顺序：后耳 → 前耳 → 头盖 → 眼睛（耳根压进头盖下，与参考图一致）。
// 脸件与参考图同画布 1:1（鼻孔 242,340 同位）；眼件 0.1215 → (78,185) 48×65（IoU 0.995）；
// 前耳 0.1159 → 参考左耳 (12,0) 68×117（IoU 0.946）；后耳 0.1241 对齐参考右耳后下移 10px 至 (102,18)，
// 让根部整段压在头盖下（参考图里背耳在脸的下层；原对齐位右下角探出脸缘、与脸顶之间露白缝）。
// 注：file 仅记录原素材文件名（溯源），运行时按 key 拼 parts-horse/<key>.png，不读此字段。
import type { PartDef } from "./horse-manifest";

export const HORSE_HEAD_W = 320;
export const HORSE_HEAD_H = 431;

export const PARTS_HORSE_HEAD: Record<string, PartDef> = {
  head: { file: "ma-nian.png", x: 0, y: 0, w: 320, h: 431 },
  ear_front: { file: "ma-erduo-qianmian.png", x: 12, y: 0, w: 68, h: 117 },
  ear_back: { file: "ma-erduo-houmian.png", x: 102, y: 18, w: 61, h: 111 },
  eye_normal: { file: "ma-yanjing-zhengchang.png", x: 78, y: 185, w: 48, h: 65 },
};

export const HORSE_HEAD_ORDER = ["ear_back", "ear_front", "head", "eye_normal"] as const;
