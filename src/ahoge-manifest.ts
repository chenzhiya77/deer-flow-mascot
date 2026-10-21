// 呆毛独立件（Hya-daimao，黑描边透明底）。主体已换为无呆毛版 Hya-wudaimaozhuti.png。
// 落位按拆件前在主体里的可见位置拟合：主体坐标 (749,331) 159×118，IoU 0.872。
import type { PartDef } from "./parts-user-manifest";

export const PARTS_AHOGE: Record<string, PartDef> = {
  ahoge: { file: "Hya-daimao.png", x: 842, y: 335, w: 159, h: 118 },
};

// 呆毛落在帽檐之后：按新主体帽檐下缘（-2px 叠进黑边）裁掉尖端，避免戳进帽檐的棕色面。
export const AHOGE_CLIP =
  "polygon(0px 30px, 11px 26px, 31px 17px, 51px 9px, 71px 2px, 91px 0px, 159px 0px, 159px 118px, 0px 118px)";
