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

### 静帧（11 个）

| 组 | Stills | 尺寸 |
| --- | --- | --- |
| `CowboyCutUser` | rest / wave / blink / rest+wuyu / rest+zhuangsha / rest+miyanxiao / rest+hengmiyanxiao | 1856×1280 |
| `HorseCut` | rest / step | 1856×1280 |
| `RidingCut` | rest / ride | 1856×1280 |

## 目录结构

```
src/
  Root.tsx                 全部 Composition / Still 注册
  CowboyCutUser.tsx        DuckRig：主装配件（姿态变换、near/far 分层、眼态切换）+ 静帧组件
  HorseCut.tsx             HorseRig：马装配件（rest/step，含挂载槽位）
  RidingCut.tsx            骑乘合成：白底 + 地面阴影 + 马 + 分层坐进去的鸭
  WalkVideo / DuckWalk / DuckJump / DuckFall / MountUp / ThinkScratch   单场景组件
  parts-user-manifest.ts   切件定位表（scripts/align_pieces.py 生成）
  eye-states-manifest.ts   眼态库：normal / wuyu / zhuangsha / miyanxiao / hengmiyanxiao
  horse-manifest.ts        马分件定位表（scripts/align_horse.py 生成）
  seat-config.ts / seat-solver.ts / horse-topline.ts      座位求解
public/
  parts-user/  parts-horse/        分件 PNG
scripts/                 一次性素材工具（见下）
```

## 分件机制

- **切件**：`parts-user/` 是按原画整图精确对位的切件，全部动画与静帧都走它（叠加眼态库）。
- **姿态分层**：每个 pose 分 `body`（整体变换，轴心在座位锚点）、`local`（单件变换）、`planted`（钉地件反向抵消身体变换）。
- **near/far 分层**：`DuckRig` 按身体中线 `splitAt` 把身/腰带/眼/喙切成前后两半（各让 16px 重叠防旋转透缝）；`RidingCut` 把 far 层压在马身后、near 层盖在马身前，鸭「坐进」马背。
- **座位求解**（`seat-solver.ts`）：鸭的稳定点（身体底边中点 + 切件平移）沿马背轮廓线 `HORSE_TOPLINE` 取列，反解 `ty` 落在鞍沿。手填 `ty` 必穿模，所以由求解器算。
- **眼态库**（`eye-states-manifest.ts`）：`EYE_SWAP` 把 normal / wuyu / zhuangsha / miyanxiao / hengmiyanxiao 映射到左/右眼件；wuyu、zhuangsha、miyanxiao、hengmiyanxiao 为素材眼，按眼白 / 板框实测落位，一次算好永久复用。
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