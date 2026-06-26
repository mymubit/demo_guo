# 12 角色设计说明（v3.1）

> 本文档说明当前 12 角色体系的设计 rationale。配置 SSOT：`registry.yaml` + `roles/*/role.yaml`。

## 设计目标

1. **覆盖完整短剧流水线**：立项 → 设定 → 大纲 → 剧本 → 审查 → 合规 →（可选）精修与发行
2. **控制认知负担**：默认 8 步快速通道；4 个 composite 角色按需启用
3. **规则集中治理**：角色薄、规则厚；不在 12 份 SKILL 正文重复方法论

## 角色分层

| 类型 | 数量 | 含义 |
|------|------|------|
| `core` | 8 | 快速通道必经；每个项目至少走一遍 |
| `composite` | 4 | 整合多模块能力；专家通道或专项增强 |

## 部门划分（虚拟编组）

仅用于导航与 `expert-track.yaml` 分 phase，不影响规则加载逻辑。

| dept | 角色 |
|------|------|
| strategy | topic-planner, market-analyst |
| worldbuilding | world-architect, character-designer |
| plot_engine | plot-architect, narrative-engineer |
| writing | script-writer |
| review | script-reviewer, quality-reporter |
| polish | polish-master |
| production | production-pack |
| ops | compliance-guard |

## Composite 与 modules

| 角色 | modules | 能力摘要 |
|------|---------|----------|
| market-analyst | market-radar, formula-analysis, tear-down-6d | 市场趋势 + 爆款公式 + 六维拉片 |
| narrative-engineer | emotion-blueprint, hook-system, conflict-escalation, reversal-system, psychology-immersion | 大纲后叙事深度强化 |
| polish-master | dialogue-polish, format-fix, word-count-governance, storyboard-9col | 台词/格式/字数/分镜一站式 |
| production-pack | visual-anchor, marketing-copy, delivery-check, story-to-game | 视觉/营销/交付/互动游戏 |

模块正文：`modules/*.md`。

## 产物依赖（Artifact DAG）

```
project_brief
  → world_setting, character_bible
    → series_outline
      → [narrative_plan]
      → episode_scripts
        → review_report, quality_report, compliance_report
        → [polished_script] → [production_package]
```

各边定义在对应 `role.yaml` 的 `input_contract` / `output_contract`。

## 关键设计决策

| 决策 | 理由 |
|------|------|
| script-writer 分批 `episode_range` | 控制 token；LR-008 逐集上下文 |
| compliance-guard 走 compliance_block | P0 熔断独立于创作规则 |
| 数值不进 SKILL 正文 | 统一引用 `script-format.yaml` |
| SKILL.md 瘦身 | Cursor 入口；契约以 role.yaml 为准 |

## 扩展指南

- **新增 core 角色**：改 `registry.yaml`、新建 `roles/<slug>/`、补充 `stage-playbook.yaml` 条目
- **新增题材**：`foundation/rules/genres/<code>.yaml` + 更新 `theme-templates.md`
- **新增 LR**：`foundation/rules/learned-rules.yaml`
