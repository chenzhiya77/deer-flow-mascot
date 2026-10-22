# horse-head

独立马头装配快照（2026-10-22）。

## 包含

- `horse-head.png` — 透明底装配图（正常眼），320×431；alpha 触四边，裁切版与整图相同
- `horse-head-surprised.png` — 同画布吃惊眼
- `pieces/` — 5 个分件：后耳、前耳、头盖、正常眼、吃惊眼
- `manifest.json` — 基础 3 层 + `eyeStates`（normal / surprised）眼睛层；`sourceFiles` 记录原素材文件名
- `assemble.py` — 独立重拼脚本（需 Pillow）：`python assemble.py [out.png] [--eye normal|surprised]`

## 重新拼合

```console
python assemble.py out.png --eye normal
python assemble.py out-surprised.png --eye surprised
```

按 `manifest.json` 的层级与 `rect`，从 `pieces/` 重拼到 320×431 透明画布；眼睛层由 `--eye` 选择。

## 层级

后耳 → 前耳 → 头盖 → 眼睛；耳根压在头盖下，与参考图 `ma-tou.png` 一致。

## 眼睛状态

| 状态 | 件 | 落位 | 说明 |
| --- | --- | --- | --- |
| normal | `pieces/eye_normal.png` | (78,185) 48×65 | 原正常眼，件 0.1215 缩放 |
| surprised | `pieces/eye_surprised.png` | (56,170) 85×96 | 吃惊眼，1:1 原生尺寸 |

吃惊眼参考图为 644×874（同画布 2×），换算回 320×431 后环 bbox 为 (56,170) 85×97，与件 85×96 一致；瞳孔 31×34 两图相同，故按 1:1 落在 (56,170)。

## 说明

- 本包是快照；运行时真源仍是 `public/parts-horse/` 与 `src/horse-head-manifest.ts`。
- 坐标即参考图 `ma-tou.png` 的 320×431 画布；头盖 1:1，正常眼 0.1215、前/后耳 0.1159/0.1241 缩放落位。
- 只有马头，不含马身与骑乘；鸭的最终形态在 `assets/final-duck/`，马鞍单件在 `assets/horse-saddle/`。

## 自校验

从 `pieces/` 与 `manifest.json` 重拼，与 `npx remotion still HorseHead` / `npx remotion still HorseHeadSurprised` 的渲染图对比：

- normal：透明度 IoU 0.9999，平均色差 0.62/255（耳件缩放重采样所致）
- surprised：透明度 IoU 0.9999，平均色差 0.52/255

吃惊眼对参考图 1× 画布（644×874 按 1/2 缩到 320×431 后对齐）：环心偏 (0.4, −0.7) px，瞳孔心偏 (−0.5, −0.6) px。
