# 知识规则区块索引（v5.0）

> 规则 SSOT：`foundation/rules/`。本文档说明 **section 名** 与角色的注入关系。
> 角色侧通过 `role.yaml` → `rule_policy.scopes` 控制加载哪些 scope。

## 四 Scope

| Scope | YAML 标记 | 目录/文件 | 说明 |
|-------|-----------|-----------|------|
| `global_core` | `tier: 1` | `foundation/rules/*.yaml`（根级） | 全题材通用铁律 |
| `genre_profile` | `tier: 2` | `foundation/rules/genres/*.yaml` | 按 `theme_code` 过滤（由 `theme-matrix.yaml` 解析） |
| `stage_playbook` | `tier: 3` | `foundation/rules/stage-playbook.yaml` | 按 `scope_key=agent_id` |
| `compliance_block` | `tier: 4` | `foundation/rules/compliance-core.yaml` | 合规熔断 |

长文参考：`knowledge/craft/tier2-genre-rules.md`、`knowledge/craft/tier3-stage-rules.md`、`knowledge/quality/tier4-compliance.md`。

## 角色 ↔ Section 映射（4 生产 + 3 质检 + 1 工具）

| Agent | Sections |
|-------|----------|
| drama.topic-director | philosophy, concept_development, rhythm_rules, episode_structure, learned_rules |
| drama.story-bible | philosophy, character_rules, world_rules, series_structure, emotion_externalization_dict, episode_structure, rhythm_rules, foreshadowing_rules, qdn_emotion_model, payment_checkpoint_3card, conflict_escalation, originality_rules, learned_rules |
| drama.episode-designer | episode_card, episode_emotion_8nodes, qdn_emotion_model, hook_effectiveness, emotion_externalization_dict, episode_structure, rhythm_rules, foreshadowing_rules, conflict_escalation, payment_checkpoint_3card, learned_rules |
| drama.script-writer | episode_structure, continuity, production_feasibility, quantitative_constraints, writing_prohibitions, writing_requirements, information_asymmetry_mechanics, emotion_externalization_dict, ai_tone_forbidden, dialogue_craft, qdn_emotion_model, format_standard, hook_effectiveness, episode_emotion_8nodes, dialogue_quality, learned_rules |
| drama.script-scorer | scoring, continuity, world_rules, format_standard, episode_structure, character_rules, hook_effectiveness, payment_checkpoint_3card, learned_rules |
| drama.compliance-guard | compliance_block, originality_rules, learned_rules |
| drama.revision-master | writing_prohibitions, writing_requirements, ai_tone_forbidden, emotion_externalization_dict, dialogue_quality, rhythm_rules, quantitative_constraints, format_standard, learned_rules |
| drama.delivery-tool | production_feasibility, budget_estimation, platform_ops, platform_specific, three_phase_compliance_checklist, format_standard, dialogue_quality, hook_effectiveness, scoring, foreshadowing_rules, learned_rules |

> v5 变更：`drama.story-bible` 的 sections = 原人物关系官 ∪ 原全剧架构官（合并，能力零丢失）。

## Section 定义（v5.1 规则文件按主题合并为 8 个 global 文件）

| 规则文件 | 承载 sections | 中文主题 |
|---------|--------------|----------|
| `philosophy.yaml` | philosophy | 创作哲学（横截面 / McKee 价值转变） |
| `narrative-craft.yaml` | episode_structure, episode_emotion_8nodes, information_asymmetry_mechanics, emotion_externalization_dict, qdn_emotion_model, hook_effectiveness | 叙事工艺 |
| `rhythm-rules.yaml` | rhythm_rules | 节奏基线 |
| `character-rules.yaml` | character_rules | 角色逻辑（年龄决策 / 密度 / 弧光） |
| `dialogue-rules.yaml` | dialogue_quality, dialogue_craft, ai_tone_forbidden | 台词规则 |
| `writing-rules.yaml` | writing_requirements, writing_prohibitions | 写作规则 |
| `plotting-rules.yaml` | conflict_escalation, foreshadowing_rules, payment_checkpoint_3card | 情节工程 |
| `scoring-core.yaml` | scoring | 评分规范 |
| `learned-rules.yaml` | learned_rules | 经验规则 LR |
| `stage-playbook.yaml`（tier 3） | 按 agent scope_key | 阶段 playbook |
| `compliance-core.yaml`（tier 4） | p0_categories, p1_categories, p2_advisories, nine_dimension_risk_assessment, justice_tail_rule, values_bottom_line, title_compliance_rules, platform_specific, three_phase_compliance_checklist, fuse_behavior | 合规熔断 |
| `originality-rules.yaml`（tier 1） | originality_rules | 原创性保护 |
| `concept-rules.yaml`（tier 1） | concept_development | 核心概念形成 |
| `structure-rules.yaml`（tier 1） | series_structure, episode_card, continuity | 全剧结构、分集卡与连续性 |
| `world-rules.yaml`（tier 1） | world_rules | 世界规则 |
| `production-rules.yaml`（tier 1） | production_feasibility, budget_estimation, platform_ops | 制片可行性、预算分级与平台上架 |
| `genre-profile.yaml` + `genres/matrix.yaml`（tier 2） | genre_rules, rhythm_rules（四轴合成） | 题材规则 |

> `quantitative_constraints` / `format_standard` 两个 section 的数值来自 `foundation/constraints/script-format.yaml`，由后端注入时合成，不在规则文件中重复。

## 数值 SSOT

字数、场景数、台词占比 → **`foundation/constraints/script-format.yaml`**；
评分维度、权重、等级阈值 → **`foundation/constraints/quality-scoring.yaml`**；
商业公式 → **`foundation/constraints/commercial-formulas.yaml`**；
结构缩放 → **`foundation/constraints/series-scale.yaml`**。
禁止在其他文件硬编码上述数值。
