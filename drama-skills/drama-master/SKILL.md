---
name: drama-master
version: "2.0.0"
description: "AI短剧创作总入口。从零创作/断点续写/单阶段专项，智能路由到33个专业角色（含drama-intake/drama-master共35文件）。Invoke when user wants full drama creation, stage routing, or needs help getting started."
tags: ["总入口", "创作", "路由", "全流程"]
platforms: [cursor, codex, trae]
input_schema:
  - name: request
    type: string
    required: true
    description: "用户需求描述"
  - name: stage
    type: string
    required: false
    enum: [full, strategy, worldbuilding, plot, writing, review, polish, production, compliance]
    description: "指定阶段，不填则智能路由"
output_schema:
  - name: plan
    type: object
    description: "创作计划（角色分工+执行顺序）"
  - name: artifacts
    type: array
    description: "各阶段产物列表"
---

# Drama Master — AI短剧创作总入口 v2.0

## 启动方式

```
@drama-master 我要创作一部30集复仇短剧
@drama-master [hook-designer] 设计开篇钩子
@drama-master --stage=review 审查这份剧本
```

不指定角色时，显示启动问卷，引导用户完成创作配置。

---

## 启动问卷（首次创作必填）

```
① 题材类型：[都市/古代/玄幻/商战/甜宠/复仇/逆袭/悬疑/...]
② 集数规模：[短集10-20 / 标准30-40 / 长集50-80 / 其他]
③ 目标平台：[抖音 / 快手 / 微信小程序 / 通用]
④ 创作起点：[从零 / 有核心创意 / 有大纲 / 有参考作品 / 改编IP]
⑤ 特殊要求：[指定受众/风格/卖点/对标作品]
```

---

## 阶段路由

| 阶段 | 角色链 | 输出 |
|------|--------|------|
| **strategy** | market-radar → formula-analyst → topic-planner → project-reviewer | 立项简报 |
| **worldbuilding** | world-architect → character-designer → dream-analyst | 世界观+人物小传 |
| **plot** | plot-architect → [hook/conflict/reversal/rhythm/psychology] | 分集大纲+情绪曲线 |
| **writing** | script-writer + dialogue-expert + scene-director | 03_完整剧本/ |
| **review** | script-reviewer + reader-reviewer + emotion-auditor → quality-reporter | 质量报告 |
| **polish** | script-editor → pacing-optimizer → formatter | 润色后剧本 |
| **production** | visual-producer + storyboard-director + marketing-officer | 制作包+宣发物料 |
| **compliance** | compliance-guard | 合规报告 |
| **full** | strategy → worldbuilding → plot → writing → review → [polish] → production → compliance | 完整交付包 |

---

## 角色调用语法

| 平台 | 语法 |
|------|------|
| Cursor | `@drama-master [角色名] 需求` 或 `@drama-hook-designer 设计钩子` |
| Codex | `[hook] 需求` 或 `@drama-hook-designer` |
| Trae | "用钩子设计师帮我..." 或自然语言描述需求 |

**角色名速查（33个，按流程顺序）**：

战略选题：`market-radar` · `formula-analyst` · `topic-planner` · `project-reviewer` · `lapian-analyst` · `ip-adapter`

世界构建：`world-architect` · `character-designer` · `dream-analyst`

剧情引擎：`emotion-architect`【大纲前蓝图】 · `plot-architect` · `hook-designer` · `conflict-engine` · `reversal-master` · `rhythm-designer`【大纲中规划】 · `psychology-architect`

创作执行：`script-writer` · `dialogue-expert` · `scene-director`【创作阶段镜头指导】

评审质控：`script-reviewer` · `reader-reviewer` · `emotion-auditor`【剧本后检测】 · `quality-reporter`

修改润色：`script-editor` · `pacing-optimizer`【集内时长调整】 · `formatter`

制作宣发：`visual-producer` · `storyboard-director`【制作阶段九列分镜】 · `post-processor` · `marketing-officer`

合规总编室：`compliance-guard` · `evolution-analyst`

工具：`drama-intake`（外部内容摄入，非创作角色）

---

**三组易混淆角色的分工说明**：

| 组 | 角色A | 角色B | 区别 |
|----|-------|-------|------|
| 情绪 | 情绪架构师 | 节奏设计师 | 前者大纲前设蓝图，后者大纲中做规划 |
| 情绪 | 节奏设计师 | 情绪审计官 | 前者规划，后者剧本完成后检测偏差 |
| 节奏 | 节奏设计师 | 节奏优化师 | 前者全剧宏观规划，后者集内场景时长调整 |
| 镜头 | 场景导演 | 分镜导演 | 前者写作阶段提供镜头语言指导，后者制作阶段生成九列分镜表 |
| 市场 | 市场雷达 | 拉片分析师 | 前者宏观趋势，后者某部具体作品深度分析 |
| 梦境 | 爆款公式师 | 梦境指标师 | 前者选题阶段轻量预估，后者世界+人设完成后深度检测 |

---

## 交付标准

完整创作完成后，交付物必须包含：

```
output/《剧名》/
├── 02_项目设定/
│   ├── 世界观设定.md
│   ├── 人物小传.md
│   └── 分集大纲.md
├── 03_完整剧本/
│   └── *.md（按集分文件）
├── 04_评估报告/
│   └── 质量报告.json
└── 《剧名》交付包.md
```

**质量门槛**（默认值）：
- 综合评分 ≥ 80
- 格式合规 ≥ 90
- 合规检测：通过

---

## 进化说明

每次创作完成后，`evolution-analyst` 会：
1. 扫描本次创作中的亮点（钩子、反转、对白）
2. 询问用户是否归档到灵感库
3. 如质量报告有低分维度，生成技能改进提案

详见 `dept-08-ops/drama-evolution-analyst/SKILL.md`
