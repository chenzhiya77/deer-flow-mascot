# horse-legs

马的四条腿 + 尾巴，2026-10-23。分件不是手绘图，而是由脚本照整马参考图、按 `horse-upper` 的画风用代码画出来（倒角方块 + 墨线 + 纸纹），另带尾巴 10 节链摆动预览。分件 PNG 生成到 `out/horse-legs/`，不进仓库；包外素材只读不改。

## 包含

- `gen.py` — 生成 13 个分件（4 条腿 × 上段 / 下段+护箍 / 蹄 + 尾巴）→ `out/horse-legs/pieces/*.png`、`pieces.json`（每件尺寸与转轴）、`rest_full.png`（站立整马校验图）；`compose(man, pose)` 按姿态把腿、尾巴和 `horse-bust.png` 合成到 2048 参考画布
- `parts.py` — 各分件的形状与配色（段长、粗细、护箍、蹄、尾巴轮廓），尺寸量自整马参考图
- `geom.py` / `render.py` — 几何工具；倒角方块渲染（pycairo）+ 从 `../horse-upper/pieces/body.png` 借纸纹
- `compose.py` — 正向运动学（肩 / 髋 → 膝 / 飞节 → 蹄）、两段 IK、按转轴落位
- `tailrig.py` — 尾巴链：尾巴保持参考图的形状，沿平滑脊线弯曲；`chain_dev()` 给出 10 节的摆角，`MOTION` 是全部动作参数
- `tail_preview.py` — 8 秒尾巴摆动预览，时间轴与 `horse-upper/motion` 相同：慢走 → 甩头＋起跑 → 跑动
- `sheets.py` — 姿势总览 `pose_sheet.png`（6 个姿势）、分件总览 `parts_sheet.png`（标出转轴）

## 运行

```
pip install numpy opencv-python pillow pycairo
python assets/horse-legs/gen.py                          # 分件 + pieces.json + 站立校验图 → out/horse-legs/
python assets/horse-legs/sheets.py                       # 姿势总览 + 分件总览 → out/horse-legs/
python assets/horse-legs/tail_preview.py                 # 8 秒预览 → out/horse-tail-preview.mp4
python assets/horse-legs/tail_preview.py --still 1 3.4   # 单帧 → out/horse-tail-t1.png …
```

- `sheets.py` / `tail_preview.py` 找不到 `out/horse-legs/pieces.json` 时先自动生成分件（约 5 秒）。
- 预览的编码（有 ffmpeg 用 libx264 crf 18，否则 OpenCV mp4v）、`--jobs` 并行进程数（默认 2）和中文字体规则同 `horse-upper/motion/preview.py`。
- 读取：`../horse-upper/pieces/body.png`（纸纹）、`../horse-upper/horse-bust.png`（合成）、`../horse-upper/motion/`（脖子 / 鬃毛 rig、步态时间轴、版面与字体）。

## 落位（2048×2048 参考画布坐标）

| 件 | 转轴 | 段长（px） | 站立姿态 |
| --- | --- | --- | --- |
| 左前 LF / 右前 RF | 肩 (1496,1800) / (1764,1800) | 上段 317、下段 388、蹄高 125 | 竖直 |
| 左后 LH / 右后 RH | 髋 (349.6,1714) / (589,1714) | 上段 421.7、下段 403、蹄高 126 | 两段 IK 让蹄落在 (182.1,2504) / (561.5,2504)：上段 23.4° / 18.2°，下段 0° / −15.0° |
| 尾巴 | 尾根 (120,1230) | 沿轴 810 | 轴向 9° |

- 角度以屏幕顺时针为正，0° = 竖直向下；`pieces.json` 里的转轴是件内像素。
- 地面 y = 2630。图层从后到前：尾巴 → 右后 → 右前 → 左后 → 上半身（`horse-bust.png` 落 (71,−95)）→ 左前。
- 远侧腿（RF / RH）宽 0.93×、颜色压暗（×0.86 / 0.85 / 0.84），不单独画。

## 动作（尾巴，`tailrig.py` 的 `MOTION`）

| | 慢走 | 跑动 |
| --- | --- | --- |
| 整条抬起 | 0° | +50°（尾梢一段再回落 20°） |
| 每节摆幅 | 5° × 0.55 | 9° × 0.55 |
| 甩动 | 1.1 次/秒 | 2.6 次/秒 |
| 尾根晃动 | ±4° | ±4° |

- 照搬开场片 `HorseCowboy.tsx` 的尾巴链：10 节，`acc = base + 4·sin(ωT)`，逐节累加 `amp·0.55·sin(ωT − 0.75·i)`，摆动从尾根传到尾梢；原版的静态弯曲参数不用，静止时就是参考图的形状。
- 慢走 / 跑动按 `horse-upper/motion/preview.py` 的 `gblend()` 过渡；起跑时尾根先抬，每节晚 0.025 s 跟上，形成一次甩尾。
- 甩动相位按频率积分，换挡时不跳频。
- 效果：慢走尾根约 ±7°；3.4 s 前后尾根 +22°、尾梢 −7°；跑动尾根 +41°～+59°，S 形波向后飘。

## 做法

- **分件**：按参考图量的尺寸用代码画倒角方块（亮面 / 侧面 / 暗边 + 15px 墨线），叠一层从 `body.png` 借来的纸纹（腿 0.75×，比身体平滑），颜色向躯干的土黄微调；每件以关节为转轴单独输出，上段下端和下段都是圆头，膝 / 飞节弯曲时不露缝。
- **腿**：`leg_fk(root, L1, L2, a_up, a_low, a_hoof)` 正向运动学；`ik2()` 两段 IK（后腿站立、姿势总览里的着地腿用它）。
- **尾巴**：脊线切角在 10 个节点之间线性插值，等于一串切线连续的圆弧，只弯不折；每个像素保持自己的弧长和侧向偏移。脊线走在尾巴中线（尾根转轴后 110px，`gen.SPINE_N`），弯曲时两侧边缘压缩 / 拉伸程度相当，尾根和臀部的接缝不撕开。渲染逐像素反查（最近点投影），任意缩放直接出图。
- **`pose['TAIL']`** 可以是一个角度（整条刚性转）、`(lift, droop)`（尺子式弯曲，姿势总览用）或 10 个逐节角度（链式摆动）。

## 已知差异

- 预览里还没有腿；腿的步态（walk / gallop 相位与 IK，照开场片）下一步接。
- 前腿肩到地面正好 317 + 388 + 125 = 830px，伸直才着地，没有余量；步态里着地腿需要轻微拉伸分件。
- 只用于预览，还没接进 Remotion 运行时；`horse-upper` 的成品与 rig 不受影响。
