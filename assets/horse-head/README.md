# horse-head

独立马头装配快照（2026-10-22）。

## 包含

- `horse-head.png` — 透明底装配图（正常眼 + 头发），320×431；alpha 触四边，裁切版与整图相同
- `horse-head-surprised.png` — 同画布吃惊眼 + 头发
- `pieces/` — 6 个分件：后耳、前耳、头盖、头发、正常眼、吃惊眼
- `manifest.json` — 基础 3 层 + 头发层 + `eyeStates`（normal / surprised）眼睛层；`sourceFiles` 记录原素材文件名
- `assemble.py` — 独立重拼脚本（需 Pillow）：`python assemble.py [out.png] [--eye normal|surprised]`

## 重新拼合

```console
python assemble.py out.png --eye normal
python assemble.py out-surprised.png --eye surprised
```

按 `manifest.json` 的层级与 `rect`，从 `pieces/` 重拼到 320×431 透明画布；眼睛层由 `--eye` 选择。

## 层级

后耳 → 前耳 → 头盖 → 头发 → 眼睛；耳根压在头盖下，与参考图 `ma-tou.png` 一致。

头发画在头盖之上、但用 `clipPolygon` 前耳右缘裁切（发层局部 x=10、y=39 对应前耳右缘与耳根），让前耳压住发根、背耳被头发盖住，与戴发参考一致。

## 分件落位

| 件 | 落位 | 说明 |
| --- | --- | --- |
| 头盖 | (0,0) 320×431 | 1:1 |
| 前耳 | (12,0) 68×117 | 0.1159 缩放 |
| 后耳 | (102,18) 61×111 | 0.1241 缩放，根部下移 10px 压进头盖 |
| 头发 | (70,78) 113×83 | 0.909 缩放，按戴发参考（317×420 ≈ 0.865 画布）换算 |
| 正常眼 | (78,185) 48×65 | 0.1215 缩放 |
| 吃惊眼 | (56,170) 85×96 | 1:1 |

## 眼睛状态

| 状态 | 件 | 落位 | 说明 |
| --- | --- | --- | --- |
| normal | `pieces/eye_normal.png` | (78,185) 48×65 | 原正常眼，件 0.1215 缩放 |
| surprised | `pieces/eye_surprised.png` | (56,170) 85×96 | 吃惊眼，1:1 原生尺寸 |

吃惊眼参考图为 644×874（同画布 2×），换算回 320×431 后环 bbox 为 (56,170) 85×97，与件 85×96 一致；瞳孔 31×34 两图相同，故按 1:1 落在 (56,170)。

## 头发

参考图 317×420（马头约 0.865 缩放，带脖子），用眼/鼻孔中心求出参考→320×431 的相似变换；发件 124×91 按填充 IoU 拟合：0.909 → (70,78) 113×83，对参考 1× 画布的头发填充 IoU 0.82（参考含发下阴影，面积略大）。无旋转拟合更优（旋转 −6° 时 IoU 0.76）。

## 说明

- 本包是快照；运行时真源仍是 `public/parts-horse/` 与 `src/horse-head-manifest.ts`。
- 坐标即参考图 `ma-tou.png` 的 320×431 画布；头盖 1:1，头发 0.909，正常眼 0.1215、前/后耳 0.1159/0.1241 缩放落位。
- 只有马头，不含马身与骑乘；鸭的最终形态在 `assets/final-duck/`，马鞍单件在 `assets/horse-saddle/`，马身上半身静态装配在 `assets/horse-upper/`。

## 自校验

从 `pieces/` 与 `manifest.json` 重拼，与 `npx remotion still HorseHead` / `npx remotion still HorseHeadSurprised` 的渲染图对比：

- normal：透明度 IoU 0.9999，平均色差 0.63/255（耳件缩放重采样所致）
- surprised：透明度 IoU 0.9999，平均色差 0.53/255

吃惊眼对参考图 1× 画布（644×874 按 1/2 缩到 320×431 后对齐）：环心偏 (0.4, −0.7) px，瞳孔心偏 (−0.5, −0.6) px。
