// 眼态定位表（表情库）：每条记录 = 件文件 + 在鸭脸上的 x/y/w/h，算一次永久复用。
// 对位按眼白 / 板框实测，同手绘尺度 S=73/295（原眼 2.hya-yanjing.png 的显示缩放）。
// 命名：用户素材的「左/右」按图侧（zuoyan→eye_0，与 zuojiao→boot_l 同规矩）。
// 共用件（无语）左右各落一份同名副本、不镜像。
// 注：file 仅记录原素材文件名（溯源），运行时按 key 拼 parts-user/<key>.png，不读此字段。
import type { PartDef } from "./parts-user-manifest";

export type EyeState = "normal" | "wuyu" | "zhuangsha";

// 无语（hya-无语-共用，左右同件不镜像；瞳仁质心实测与件同向）。
// 位置按他给的参考图 无语参考.png 实测对位：参考与源件身体方块同宽（713 vs 714 ⇒ 尺度 1.0），
// 按喙心/身块中线换算 dx=-127、dy=+2 ⇒ 眼板框 duck-space 左 (549.6,549.6) 右 (995.1,549.6)、143.8×94.8
// （参考板底 644 与原眼底 643 平；板间距 445.5 ≈ 原眼间距 446）。
// 高光锚定对这种「白眼球大板」风格不成立（会偏 ~-38/-29），眼板框对齐才准。
const PARTS_WUYU: Record<string, PartDef> = {
  eye_0_wuyu: { file: "hya-无语-共用.png", x: 549.6, y: 549.6, w: 143.8, h: 94.8 },
  eye_1_wuyu: { file: "hya-无语-共用.png", x: 995.1, y: 549.6, w: 143.8, h: 94.8 },
};

// 装傻（hya-装傻-左 / hya-装傻 -右，右件文件名「傻」后带空格）：左右件、瞳仁互为镜像朝内（对眼），
// 左件→eye_0、右件→eye_1 自然对位即与参考同向，无需再镜像。
// 位置按参考图 装傻参考.png 实测：喙宽 371＝源件 371（尺度 1.0）、dx=-128、dy=0；
// 白眼球 sclera 框 duck-space 左 (557,512,150×154) 右 (951,511,152×155)（眼距 395，比原眼距 446 近＝呆滞对眼）；
// sclera 尺寸＝件 × S=73/295 又吻合（608×S=150.5 / 613×S=151.7）⇒ 同手绘尺度。
const PARTS_ZHUANGSHA: Record<string, PartDef> = {
  eye_0_zhuangsha: { file: "hya-装傻-左.png", x: 544.5, y: 499.9, w: 179.4, h: 181.2 },
  eye_1_zhuangsha: { file: "hya-装傻 -右.png", x: 938.4, y: 499.7, w: 179.4, h: 181.7 },
};

export const PARTS_EYES: Record<string, PartDef> = {
  ...PARTS_WUYU,
  ...PARTS_ZHUANGSHA,
};

export const EYE_SWAP: Record<EyeState, Record<string, string>> = {
  normal: {},
  wuyu: { eye_0: "eye_0_wuyu", eye_1: "eye_1_wuyu" },
  zhuangsha: { eye_0: "eye_0_zhuangsha", eye_1: "eye_1_zhuangsha" },
};
