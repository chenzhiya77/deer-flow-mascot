# horse-head

独立马头装配快照（2026-10-22）。

## 包含

- `horse-head.png` — 透明底装配图，320×431；alpha 触四边，裁切版与整图相同
- `pieces/` — 4 个分件：后耳、前耳、头盖、正常眼
- `manifest.json` — 从后到前的 4 层与落位；`sourceFiles` 记录原素材文件名
- `assemble.py` — 独立重拼脚本（需 Pillow）：`python assemble.py [out.png]`

## 重新拼合

```console
python assemble.py out.png
```

按 `manifest.json` 的层级与 `rect`，从 `pieces/` 重拼到 320×431 透明画布。

## 层级

后耳 → 前耳 → 头盖 → 眼睛；耳根压在头盖下，与参考图 `ma-tou.png` 一致。

## 说明

- 本包是快照；运行时真源仍是 `public/parts-horse/` 与 `src/horse-head-manifest.ts`。
- 坐标即参考图 `ma-tou.png` 的 320×431 画布；头盖 1:1，眼件 0.1215、前/后耳 0.1159/0.1241 缩放落位。
- 只有马头，不含马身与骑乘；鸭的最终形态在 `assets/final-duck/`，马鞍单件在 `assets/horse-saddle/`。

## 自校验

从 `pieces/` 与 `manifest.json` 重拼，与 `npx remotion still HorseHead` 的渲染图对比：透明度 IoU 0.9999，平均色差 0.92/255（耳件缩放重采样所致）。
