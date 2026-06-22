---
name: drama-master
version: "2.0.0"
description: "AI短剧创作总入口。从零创作/断点续写/单阶段专项，智能路由到27个专业角色。Invoke when user wants full drama creation, stage routing, or needs help getting started."
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

**角色名速查**：
`market-radar` · `formula-analyst` · `topic-planner` · `project-reviewer`
`world-architect` · `character-designer` · `dream-analyst`
`plot-architect` · `hook-designer` · `conflict-engine` · `reversal-master` · `rhythm-designer` · `psychology-architect`
`script-writer` · `dialogue-expert` · `scene-director`
`script-reviewer` · `reader-reviewer` · `emotion-auditor` · `quality-reporter`
`script-editor` · `pacing-optimizer` · `formatter`
`visual-producer` · `storyboard-director` · `marketing-officer`
`compliance-guard` · `evolution-analyst`

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
