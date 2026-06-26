# 知识规则区块索引（v3.1）

> 规则 SSOT：`foundation/rules/`。本文档说明 **section 名** 与 **12 角色** 的注入关系。
> 角色侧通过 `role.yaml` → `rule_policy.scopes` 控制加载哪些 scope。

## 四 Scope

| Scope | YAML 标记 | 目录/文件 | 说明 |
|-------|-----------|-----------|------|
| `global_core` | `tier: 1` | `foundation/rules/*.yaml`（根级） | 全题材通用铁律 |
| `genre_profile` | `tier: 2` | `foundation/rules/genres/*.yaml` | 按 `theme_code` 过滤（由 `theme-matrix.yaml` 解析） |
| `stage_playbook` | `tier: 3` | `foundation/rules/stage-playbook.yaml` | 按 `scope_key=agent_id` |
| `compliance_block` | `tier: 4` | `foundation/rules/compliance-core.yaml` | 合规熔断 |

长文参考：`knowledge/tier2-genre-rules.md`、`knowledge/tier3-stage-rules.md`、`knowledge/tier4-compliance.md`。

## 12 角色 ↔ Section 映射

| Agent | Sections |
|-------|----------|
| drama.topic-planner | philosophy |
| drama.market-analyst | rhythm_rules, philosophy, scoring, episode_structure, learned_rules |
| drama.world-architect | philosophy |
| drama.character-designer | philosophy, foreshadowing_rules, character_rules |
| drama.plot-architect | episode_structure, rhythm_rules, quantitative_constraints, foreshadowing_rules, qdn_emotion_model, hook_effectiveness, payment_checkpoint_3card, conflict_escalation, learned_rules |
| drama.narrative-engineer | episode_emotion_8nodes, qdn_emotion_model, hook_effectiveness, emotion_externalization_dict, episode_structure, rhythm_rules, foreshadowing_rules, conflict_escalation, learned_rules |
| drama.script-writer | episode_structure, quantitative_constraints, writing_prohibitions, writing_requirements, information_asymmetry_mechanics, emotion_externalization_dict, ai_tone_forbidden, qdn_emotion_model, format_standard, hook_effectiveness, episode_emotion_8nodes, dialogue_quality, learned_rules |
| drama.polish-master | writing_prohibitions, writing_requirements, ai_tone_forbidden, emotion_externalization_dict, dialogue_quality, rhythm_rules, quantitative_constraints, format_standard, learned_rules |
| drama.script-reviewer | scoring, format_standard, learned_rules |
| drama.quality-reporter | scoring, learned_rules |
| drama.production-pack | format_standard, dialogue_quality, hook_effectiveness, scoring, foreshadowing_rules, learned_rules |
| drama.compliance-guard | （主体走 compliance_block scope） |

## Section 定义

| section | 中文名 | 规则文件 |
|---------|--------|----------|
| `philosophy` | 创作哲学 | `philosophy.yaml` |
| `rhythm_rules` | 节奏规则 | `rhythm-rules.yaml` |
| `episode_structure` | 分集结构 | `narrative-craft.yaml`、`stage-playbook.yaml` |
| `episode_emotion_8nodes` | 8 节点情绪 | `narrative-craft.yaml` |
| `foreshadowing_rules` | 伏笔规则 | `foreshadowing-rules.yaml` |
| `scoring` | 评分规范 | `scoring-core.yaml` |
| `quantitative_constraints` | 量化约束 | `script-format.yaml`（数值）+ `writing-*.yaml` |
| `writing_prohibitions` | 写作禁止 | `writing-prohibitions.yaml` |
| `writing_requirements` | 写作要求 | `writing-requirements.yaml` |
| `information_asymmetry_mechanics` | 信息差机制 | `narrative-craft.yaml` |
| `emotion_externalization_dict` | 情绪外化 | `narrative-craft.yaml` |
| `ai_tone_forbidden` | AI 腔禁用 | `ai-tone-forbidden.yaml` |
| `qdn_emotion_model` | QDN 情绪模型 | `narrative-craft.yaml` |
| `format_standard` | 格式规范 | `script-format.yaml` |
| `hook_effectiveness` | 钩子有效性 | `narrative-craft.yaml` |
| `dialogue_quality` | 对白质量 | `dialogue-voice.yaml` |
| `character_rules` | 角色逻辑 | `character-logic.yaml` |
| `payment_checkpoint_3card` | 付费三卡 | `payment-checkpoint.yaml` |
| `conflict_escalation` | 冲突升级 | `conflict-escalation.yaml` |
| `learned_rules` | 经验规则 LR | `learned-rules.yaml` |

## 数值 SSOT

字数、场景数、台词占比、评分阈值 → **`foundation/constraints/script-format.yaml`**（禁止在其他文件硬编码）。
