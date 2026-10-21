# horse-saddle

马鞍单件素材快照（2026-10-22）。

## 包含

- `saddle.png` — 透明底单件，842×596；alpha 触四边，无裁切余量
- `manifest.json` — 单层记录、原素材名与挂载状态

## 说明

- 单层件，不需要 `assemble.py`；直接使用 `saddle.png`。
- 当前未挂到马身：`HorseCut` / `RidingCut` 里的马鞍是烘在 `public/parts-horse/body.png` 中的。本包只归档独立件。
- 原始文件：`ma-maan.png`。
- 如果后续要替换马身上的鞍，需要先确定在 1856×1280 场景里的落位与缩放，再把本件作为身体上层叠加；届时可在这里补 `rect` / assembler。
- 鸭的最终形态在 `assets/final-duck/`，马头在 `assets/horse-head/`。
