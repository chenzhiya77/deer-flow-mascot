# final-duck

「鸭牛仔」最终形态素材快照（2026-10-22）。

## 包含

- `duck-final-1856x1280.png` — 透明底整图，画布 1856×1280
- `duck-final.png` — 裁切版 1392×1280（原画布 x 204–1595，上下保留整高）
- `pieces/` — 15 个最终形态分件：身体（无呆毛）、呆毛、正常眼、上下嘴、手、脚、仙人掌腰带、方巾
- `eyes/` — 9 种眼态 × 左右两件：normal / wuyu / zhuangsha / miyanxiao / hengmiyanxiao / renzheng / daimeng / xiakan / yanbai
- `manifest.json` — 从后到前的 15 层，含每件在 1856×1280 画布上的落位；呆毛层带 `clipPolygon`（帽檐裁剪）；`eyeStates` 记录每种眼态的左右件与落位
- `assemble.py` — 独立重拼脚本（需 Pillow）：`python assemble.py [out.png] [--eyes STATE]`

## 重新拼合

```console
python assemble.py out.png                  # 默认 normal 眼
python assemble.py out-wuyu.png --eyes wuyu
```

按 `manifest.json` 的层级、`rect` 与 `clipPolygon` 从 `pieces/` 与 `eyes/` 重拼到 1856×1280 透明画布；裁切版对应 `images.trimmedBounds`。

## 形态

rest 站姿 + 正常眼 + 上下嘴闭合 + 仙人掌腰带 + 方巾。牛仔帽已烘在身体件里，不单独拆件。

## 说明

- 本包是快照；运行时真源仍是 `public/parts-*` 与 `src/*-manifest.ts`。
- 呆毛独立成件（`pieces/ahoge.png`），装配时按 `clipPolygon` 裁掉帽檐上方的尖端；如需让呆毛飘出帽檐，需把帽子也拆成独立上层。
- 旧整嘴 `public/parts-user/beak.png` 仍在仓库里，是 `mouth: "normal"` 的默认嘴态，本包不含。
- 动作 rig（按开场片 `duckPose` 摆分件、骑乘前后分层）和开场片的五个关键帧见 `motion/`。
- 马不在此包（`motion/` 的关键帧用 `assets/horse-legs/` 的整马）；拼好的马头快照见 `assets/horse-head/`，马鞍单件见 `assets/horse-saddle/`，马身上半身静态装配见 `assets/horse-upper/`。
- 重新生成整图：`npx remotion still FinalDuck out/final-duck.png`。

## 自校验

按 `manifest.json` 从 `pieces/` 与 `eyes/` 重新拼合（含呆毛帽檐裁剪），九种眼态均与 Remotion 渲染图核对：透明度 IoU 0.9981，平均色差 4.57–4.76/255（缩放重采样所致）。
