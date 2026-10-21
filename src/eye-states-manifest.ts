// 眼态定位表（表情库）：每条记录 = 件文件 + 在鸭脸上的 x/y/w/h，算一次永久复用。
// 对位按眼白 / 板框实测，同手绘尺度 S=73/295（原眼 2.hya-yanjing.png 的显示缩放）。
// 命名：用户素材的「左/右」按图侧（zuoyan→eye_0，与 zuojiao→boot_l 同规矩）。
// 共用件（无语）左右各落一份同名副本、不镜像。
// 注：file 仅记录原素材文件名（溯源），运行时按 key 拼 parts-user/<key>.png，不读此字段。
import type { PartDef } from "./parts-user-manifest";

export type EyeState =
  | "normal"
  | "wuyu"
  | "zhuangsha"
  | "miyanxiao"
  | "hengmiyanxiao"
  | "renzheng"
  | "daimeng"
  | "xiakan"
  | "yanbai";

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

// 眯眼笑（Hya-miyanxiao，单件左右共用、不镜像；件 122×64 且左右描线对称）。
// 参考图 参考-1.png 实测：身块 714 vs 源件 715、喙 351 vs 源件 350、手 232 vs 231 ⇒ 尺度 1.0；
// 手/身统一 dx=-128、dy=+1 ⇒ 眼部 duck-space 左 (552,553) 右 (989,553)、122×64。
// 参考图两眼墨迹分别 122×64 / 120×64（右眼窄 2px 为抗锯齿），两眼距 436 比原眼 446 略近（参考原画如此）。
const PARTS_MIYANXIAO: Record<string, PartDef> = {
  eye_0_miyanxiao: { file: "Hya-miyanxiao.png", x: 552, y: 553, w: 122, h: 64 },
  eye_1_miyanxiao: { file: "Hya-miyanxiao.png", x: 989, y: 553, w: 122, h: 64 },
};

// 横眯眼笑（Hya-hengmiyanxiao-zuo / -you，左右成对、vertex 朝内，互为镜像 IoU 0.92，无需再镜像）。
// 参考图 参考-2.png 实测：两眼墨迹框 129×116 / 131×117 ≈ 件原尺寸 129×115 / 131×116 ⇒ 尺度 1.0；
// 参考身体板与 参考-1 同位（600,345）⇒ 沿用统一 dx=-128、dy=+1 ⇒ duck-space 左 (564,536) 右 (971,534)。
// 两眼距 408（比原眼 446 近，> < 向喙内收），参考原画如此。
const PARTS_HENGMIYANXIAO: Record<string, PartDef> = {
  eye_0_hengmiyanxiao: { file: "Hya-hengmiyanxiao-zuo.png", x: 564, y: 536, w: 129, h: 115 },
  eye_1_hengmiyanxiao: { file: "Hya-hengmiyanxiao-you.png", x: 971, y: 534, w: 131, h: 116 },
};

// 认真（hya-renzheng-zuo / hya-renzhen-you，右件文件名少一个 g；左件→eye_0、右件→eye_1，不镜像）。
// 源件是 4 倍稿（左 474×685、右 450×692），按 1/4 显示后墨迹框与参考图 Hya-renzheng-cankao.png
// 的 118×171 / 111×172 吻合；沿用统一 dx=-128、dy=+1 ⇒ duck-space 左 (559.5,490.5) 右 (995.5,488.5)。
// 叠图核验：左眼墨迹 IoU 0.9946、右眼 0.9905（MAD 2.03 / 2.33）。
const PARTS_RENZHENG: Record<string, PartDef> = {
  eye_0_renzheng: { file: "hya-renzheng-zuo.png", x: 559.5, y: 490.5, w: 118.5, h: 171.25 },
  eye_1_renzheng: { file: "hya-renzhen-you.png", x: 995.5, y: 488.5, w: 112.5, h: 173 },
};

// 呆萌（hya-呆萌-共用，单件左右共用、不镜像；白高光都在左上）。
// 参考图 Hya-yanjing-daimeng-cankao.png 实测：源件 454×488（4 倍稿），按 0.25 显示 113.5×122；
// 参考眼墨迹框 113×122 / 115×122，共用件统一 0.25；沿用 dx=-128、dy=+1
// ⇒ duck-space 左 (557,525) 右 (996,524)。叠图核验：左眼墨迹 IoU 0.9878、右眼 0.9914（MAD 2.38 / 2.34）。
const PARTS_DAIMENG: Record<string, PartDef> = {
  eye_0_daimeng: { file: "hya-呆萌-共用.png", x: 557, y: 525, w: 113.5, h: 122 },
  eye_1_daimeng: { file: "hya-呆萌-共用.png", x: 996, y: 524, w: 113.5, h: 122 },
};

// 下看（Hya-yj-xiakan-zuo / -you，左右成对、瞳仁朝下且向喙内；左→eye_0、右→eye_1，不镜像）。
// 参考图 Hya-xiakan-cankao.png 实测：源件 123×132 已是显示尺寸（1:1，外框墨迹 121×130），
// 参考眼外框 121×130 / 122×130；沿用 dx=-128、dy=+1 ⇒ duck-space 左 (562,518) 右 (994,518)。
// 叠图核验：外框/瞳仁位置对齐，差异只在 1–2px 描边（细环 IoU 0.871 / 0.878，MAD 7.7 / 9.3）。
const PARTS_XIAKAN: Record<string, PartDef> = {
  eye_0_xiakan: { file: "Hya-yj-xiakan-zuo.png", x: 562, y: 518, w: 123, h: 132 },
  eye_1_xiakan: { file: "Hya-yj-xiakan-you.png", x: 994, y: 518, w: 123, h: 132 },
};

// 纯眼白（Hya-yanbai-zuo / -you；无瞳仁、无方向性 ⇒ 按共用件处理：左右都用 -zuo，避免两件色差）。
// 参考图 Hya-yanbaicankao.png 实测：源件 123×131（1:1，外框墨迹 121×128）；参考眼外框 121×129 / 122×130；
// 沿用 dx=-128、dy=+1 ⇒ duck-space 左 (562,518)、右 (993,518)。
// 注：-you 件中心白比 -zuo 亮约 2.2/255、外框小 1–2px，不采用（参考图左右眼色差 <1）。
const PARTS_YANBAI: Record<string, PartDef> = {
  eye_0_yanbai: { file: "Hya-yanbai-zuo.png", x: 562, y: 518, w: 123, h: 131 },
  eye_1_yanbai: { file: "Hya-yanbai-zuo.png", x: 993, y: 518, w: 123, h: 131 },
};

export const PARTS_EYES: Record<string, PartDef> = {
  ...PARTS_WUYU,
  ...PARTS_ZHUANGSHA,
  ...PARTS_MIYANXIAO,
  ...PARTS_HENGMIYANXIAO,
  ...PARTS_RENZHENG,
  ...PARTS_DAIMENG,
  ...PARTS_XIAKAN,
  ...PARTS_YANBAI,
};

export const EYE_SWAP: Record<EyeState, Record<string, string>> = {
  normal: {},
  wuyu: { eye_0: "eye_0_wuyu", eye_1: "eye_1_wuyu" },
  zhuangsha: { eye_0: "eye_0_zhuangsha", eye_1: "eye_1_zhuangsha" },
  miyanxiao: { eye_0: "eye_0_miyanxiao", eye_1: "eye_1_miyanxiao" },
  hengmiyanxiao: { eye_0: "eye_0_hengmiyanxiao", eye_1: "eye_1_hengmiyanxiao" },
  renzheng: { eye_0: "eye_0_renzheng", eye_1: "eye_1_renzheng" },
  daimeng: { eye_0: "eye_0_daimeng", eye_1: "eye_1_daimeng" },
  xiakan: { eye_0: "eye_0_xiakan", eye_1: "eye_1_xiakan" },
  yanbai: { eye_0: "eye_0_yanbai", eye_1: "eye_1_yanbai" },
};
