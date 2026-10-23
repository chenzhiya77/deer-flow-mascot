# duck-mascot

「鸭牛仔」吉祥物分件动画（Remotion）。鸭、牛仔鸭、马的手绘分件（PNG）在代码里装配成可渲染的动作场景与静帧，用于 RAG 功能视频。

## 常用命令

```console
npm i --loglevel=error                       # 安装依赖
npm run dev                                  # Remotion Studio，实时预览所有 Composition
npx remotion render WalkVideo out/walk.mp4   # 渲染单个动画
npx remotion still RidingRest out/rest.png   # 渲染单张静帧
npm run lint                                 # eslint + tsc
```

## 场景一览

### 动画（7 个，均 1856×1280 @30fps）

| Composition | 帧数 | 内容 |
| --- | --- | --- |
| `WalkVideo` | 60（2s） | 骑乘行走循环：鸭身绕接触点跷跷板，马四腿近/远侧交替 |
| `DuckWalk` | 60（2s） | 鸭步行 |
| `DuckRun` | 60（2s） | 鸭跑步（同一组件的 `gait: "run"` 参数） |
| `DuckJump` | 60（2s） | 跳跃循环：蹬地压缩 → 伸展 → 腾空 → 落地缓冲（squash & stretch 关键帧插值） |
| `DuckFall` | 120（4s） | 高台坠落：二次加速下落带拖尾、砸地缓冲、摔懵衰减、归位 |
| `MountUp` | 90（3s） | 上马：鸭从马后跃出弧线，落点直接取座位求解值 |
| `ThinkScratchV2` | 192（6.4s） | 挠头思考：蓄力、上抬过冲、两轮挠（节奏渐快），带眼态时间线（无语 → 装傻） |

### 静帧（24 个）

| 组 | Stills | 尺寸 |
| --- | --- | --- |
| `CowboyCutUser` | rest / wave / blink / rest+wuyu / rest+zhuangsha / rest+miyanxiao / rest+hengmiyanxiao / rest+renzheng / rest+daimeng / rest+xiakan / rest+yanbai / rest+cactusBelt / rest+cactusBelt+bandana / rest+splitMouth | 1856×1280 |
| `FinalDuck` | rest+cactusBelt+bandana+splitMouth（透明底） | 1856×1280 |
| `HorseCut` | rest / step | 1856×1280 |
| `RidingCut` | rest / ride | 1856×1280 |
| `HorseHead` | normal / surprised | 320×431 |
| `Beak` | upper+lower | 1052×415 |
| `CactusBelt` | rest | 760×181 |
| `Bandana` | rest | 2120×724 |

## 最终素材包

`assets/final-duck/` 是最终形态快照：透明底整图 `duck-final-1856x1280.png`（另附裁切版 `duck-final.png`）、`pieces/` 15 个最终分件、`eyes/` 9 种眼态素材、`manifest.json`（从后到前的层级、落位与 `eyeStates`）以及 `assemble.py`（按 manifest 重拼，`--eyes` 切眼态）。运行时真源仍是 `public/parts-*`；重渲染用 `npx remotion still FinalDuck out/final-duck.png`。`assets/final-duck/motion/` 是鸭子的动作 rig 和开场片的五个关键帧（2026-10-24）：`duckrig.py` 用开场片 `duckPose` 的字段摆最终形态分件（骑乘时从身体中线分成马后 / 马前两半），`python assets/final-duck/motion/keyframes.py` 把鸭和新马放进开场片的五个时刻（站书堆 → 低头看马 → 空中一顿，开始下落 → 追马 → 骑马喊“出发！”），出开场镜头和角色特写到 `out/`（不进仓库）。

`assets/horse-head/` 是独立马头快照：透明底 `horse-head.png` / `horse-head-surprised.png`（320×431，均带头发）、`pieces/` 6 个分件（后耳 / 前耳 / 头盖 / 头发 / 正常眼 / 吃惊眼）、`manifest.json`（基础 3 层 + 头发层 + `eyeStates`）以及 `assemble.py`（按 manifest 重拼，`--eye` 切眼态）。运行时真源仍是 `public/parts-horse/` 与 `src/horse-head-manifest.ts`；重渲染用 `npx remotion still HorseHead out/horse-head.png`（吃惊眼用 `HorseHeadSurprised`）。

`assets/horse-saddle/` 是马鞍单件快照：透明底 `saddle.png`（339×240，无白边完整件）与 `manifest.json`。静态装配 `assets/horse-upper/` 已按 2.2162 / (554.2,930.9) 把它画在脖子之上；运行时 `HorseCut` / `RidingCut` 仍使用 `public/parts-horse/body.png` 中烘入的马鞍，单件保留给马鞍单独运动。

`assets/horse-upper/` 是马的上半身静态装配快照（2026-10-23）：`horse-upper.png`（躯干+马鞍+新脖子，1956×1832）、`horse-bust.png`（+马头，2542×2021）、`pieces/` 2 个源分件（躯干、新脖子）、`placements.json`（2048 参考画布落位与校验数字）以及 `assemble.py`。旧脖子背衬已移除，接缝用本地取色补齐；静态图重拼用 `python assets/horse-upper/assemble.py`，桌面参考图只用于可选校验，缺失不影响成品。`assets/horse-upper/motion/` 是脖子＋鬃毛摆动预览 rig：`python assets/horse-upper/motion/preview.py` 出 8 秒预览到 `out/`（不进仓库）。

`assets/horse-legs/` 是马的四条腿 + 尾巴（2026-10-23）：分件由代码按 `horse-upper` 的画风生成（`python assets/horse-legs/gen.py` → `out/horse-legs/`，PNG 不进仓库），`compose()` 按姿态合成整马；尾巴用开场片的 10 节链摆动，形状不变、沿平滑脊线弯曲，`python assets/horse-legs/tail_preview.py` 出 8 秒预览到 `out/`；腿照开场片的慢走 / 跑动步态走，着地的蹄锁在地面上，身上画的近侧后腿大腿跟着腿转，压在腿上的那段身体轮廓削细到接近参考图，`python assets/horse-legs/gait_preview.py` 出 8 秒步态预览。

`assets/horse-lantern/` 是开场片沙漠夜景的马灯挂到新马上的预览（2026-10-23）：灯的单摆（`lantern.ts`）和地上光斑、光晕、夜景调色照搬开场片，挂点在马鞍前下角 (1250,1395)；摆动用柔化版，只让灯感受 25% 的竖直颠簸（原参数在跑动时一直撞 ±69° 限位，开场片本身也是这样），灯体用本包的墨线画法。`python assets/horse-lantern/lantern_preview.py` 出 8 秒夜景预览到 `out/`（右边特写对比原参数 / 柔化），`--style svg` 换成开场片原版矢量灯。

## 目录结构

```
src/
  Root.tsx                 全部 Composition / Still 注册
  CowboyCutUser.tsx        DuckRig：主装配件（姿态变换、near/far 分层、眼态切换）+ 静帧组件
  HorseCut.tsx             HorseRig：马装配件（rest/step，含挂载槽位）
  RidingCut.tsx            骑乘合成：白底 + 地面阴影 + 马 + 分层坐进去的鸭
  WalkVideo / DuckWalk / DuckJump / DuckFall / MountUp / ThinkScratch   单场景组件
  parts-user-manifest.ts   切件定位表（scripts/align_pieces.py 生成）
  eye-states-manifest.ts   眼态库：normal / wuyu / zhuangsha / miyanxiao / hengmiyanxiao / renzheng / daimeng / xiakan / yanbai
  ahoge-manifest.ts        独立呆毛件：落位 + 帽檐裁剪
  horse-manifest.ts        马分件定位表（scripts/align_horse.py 生成）
  horse-head-manifest.ts   独立马头装配表：双耳 / 头盖 / 头发 / 眼睛（320×431，参考图实测）
  beak-manifest.ts         上下嘴装配表：上嘴 / 下嘴（整嘴参考 1052×399，静帧 1052×415）
  belt-manifest.ts         独立仙人掌皮带装配表：带身 / 扣子（760×181，参考图实测）
  bandana-manifest.ts      独立方巾装配表：带身 / 结+垂尾（2120×724，参考图实测）
  seat-config.ts / seat-solver.ts / horse-topline.ts      座位求解
public/
  parts-user/  parts-horse/  parts-belt/  parts-bandana/        分件 PNG
assets/final-duck/        最终形态快照：透明底整图 + 分件 + manifest.json
  motion/                 动作 rig + 开场片五个关键帧：duckrig.py / keyframes.py
assets/horse-head/        独立马头快照：双耳 / 头盖 / 头发 / 双眼态
assets/horse-saddle/      马鞍单件：无白边完整件（339×240）
assets/horse-upper/       马的上半身静态装配：躯干 + 马鞍 + 新脖子（含马头版）
  motion/                 脖子＋鬃毛摆动预览 rig：rig.py / preview.py / mane.json
assets/horse-legs/        马的四条腿 + 尾巴：代码生成分件、姿态合成、尾巴 10 节链、步态与预览
assets/horse-lantern/     马灯：开场片的马灯挂到新马上，夜景调色与摆动对比预览
scripts/                 一次性素材工具（见下）
```

## 分件机制

- **切件**：`parts-user/` 是按原画整图精确对位的切件，全部动画与静帧都走它（叠加眼态库）。
- **姿态分层**：每个 pose 分 `body`（整体变换，轴心在座位锚点）、`local`（单件变换）、`planted`（钉地件反向抵消身体变换）。
- **near/far 分层**：`DuckRig` 按身体中线 `splitAt` 把身/腰带/眼/喙切成前后两半（各让 16px 重叠防旋转透缝）；`RidingCut` 把 far 层压在马身后、near 层盖在马身前，鸭「坐进」马背。
- **座位求解**（`seat-solver.ts`）：鸭的稳定点（身体底边中点 + 切件平移）沿马背轮廓线 `HORSE_TOPLINE` 取列，反解 `ty` 落在鞍沿。手填 `ty` 必穿模，所以由求解器算。
- **眼态库**（`eye-states-manifest.ts`）：`EYE_SWAP` 把 normal / wuyu / zhuangsha / miyanxiao / hengmiyanxiao / renzheng / daimeng / xiakan / yanbai 映射到左/右眼件；wuyu、zhuangsha、miyanxiao、hengmiyanxiao、renzheng、daimeng、xiakan、yanbai 为素材眼，按眼白 / 板框实测落位，一次算好永久复用。
- **独立呆毛**（`ahoge-manifest.ts`）：主体已换成无呆毛版 `Hya-wudaimaozhuti.png`，呆毛黑描边件独立落在 `(842,335) 159×118`（按拆件前可见位置拟合，IoU 0.872）；层上带帽檐裁剪，尖端藏在帽檐后。
- **独立马头**（`horse-head-manifest.ts`）：后耳 → 前耳 → 头盖 → 头发 → 眼睛五层，坐标即参考图 `ma-tou.png` 的 320×431 画布，不挂在马身上；头盖 1:1，头发 0.909 落 (70,78) 113×83（按戴发参考换算，填充 IoU 0.82，发层按前耳右缘裁切）、正常眼 0.1215、前/后耳 0.1159/0.1241 缩放落位；眼态 `normal` / `surprised` 由 `eye` prop 切换（吃惊眼 1:1 落 (56,170) 85×96），头发由 `hair` prop 控制（默认开启）。
- **上下嘴**（`beak-manifest.ts`）：下嘴 → 上嘴两层，坐标即整嘴件 `parts-user/beak.png` 的 1052×399 画布；上嘴宽 1307→1052、纵向压到 391→310 并下移 12px（左右不变，顶弧/分缝/鼻孔对齐整嘴，向下露出下喙），下嘴按黑描边轮廓拟合（s=0.69，画布 1065×208 @ -7,201，线宽 17–18px 对齐整嘴的 18–20px），闭口时下嘴藏在上嘴之后。戴到鸭身上按整嘴件原位 `BEAK_ON_DUCK` 换算（`mouth` prop 切 normal / split）。
- **独立皮带**（`belt-manifest.ts`）：带身 → 仙人掌扣两层，坐标即参考图 `Hya-皮带-参考.png` 的 760×181 画布；带身 0.472、扣子 0.1972 缩放落位。戴到鸭身上时整张画布 ×1.25 落在 `BELT_ON_DUCK`，替换旧皮带件（`belt` prop 切 normal / cactus）。
- **独立方巾**（`bandana-manifest.ts`）：带身 → 垂尾 → 结扣三层（带身/垂尾可动、结扣为静止锚点压最上），坐标即参考图 `Hya-fangjin-cankao.png` 的 2120×724 画布；带身 1:1 原位，垂尾/结扣 0.4875 缩放落位。戴到鸭身上时整张画布 ×0.38 落在 `BANDANA_ON_DUCK`（`bandana` prop）。
- **取景定式**：单人鸭场景统一整鸭缩放 0.62、横向居中（`DuckWalk` / `DuckRun` / `DuckJump` / `ThinkScratchV2`）；`DuckFall` 独立取景（0.5）。

## 素材脚本（一次性）

随素材手工运行的工具：源素材路径写死在各自文件头（本机素材目录），换机器先改路径；产出直接写入 `public/` 与 `src/`。

| 脚本 | 作用 | 产出 |
| --- | --- | --- |
| `scripts/align_pieces.py` | 切件按原画整图对位 | `public/parts-user/` + `parts-user-manifest.ts` |
| `scripts/align_horse.py` | 马切件对位 | `public/parts-horse/` + `horse-manifest.ts` |
| `scripts/{scan,segment,measure}_cowboy.py`、`pixel_style_probe.py` | 轮廓 / 尺寸 / 风格探针（只读分析） | — |

## 约定与手调常量

- 手调常量集中在三处，改素材平移时必须跟着走，否则锚点 / 求解错位：
  - `PART_OFFSET`（切件整体平移，`seat-solver.ts`）
  - `HORSE_PART_OFFSET`（马分件平移，`horse-topline.ts`）
  - `SEAT`（座位横向 / 缩放 / 旋转，`seat-config.ts`）
- `parts-user` / `horse` / 眼态表的 `file` 字段只记录原素材文件名（溯源）；运行时按 key 拼路径取图，不读该字段。
- 帧率统一 30fps；场景画布 1856×1280，静帧 1856×1280。
- `out/`（渲染产物）与 `node_modules/` 不入库。

## License

私有项目（UNLICENSED）。Remotion 对部分组织需公司许可，见 [remotion-dev/remotion LICENSE.md](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md)。