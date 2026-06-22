# 数据完整性修复清单

> 源自 PDF 20 项审计，剔除 Fusion 专属项；每项含目标行为与验收。

---

## CRITICAL

### C1. active 唯一约束（PDF #1）

| 项 | 内容 |
|----|------|
| 问题 | `unique_together(tier, scope, section)` 阻止多 draft |
| 现状 | `SkillRuleItem`: `UniqueConstraint(rule_key, condition=active)` ✓ |
| 目标 | Config 包同样仅对 active 做条件唯一 |
| 验收 | 同一 rule_key 可存在 1 active + N draft；approve 归档旧 active |
| 测试 | `test_skill_rule_item.py` approve 用例 |

### C2. quantitative_constraints 嵌套展平（PDF #2）

| 项 | 内容 |
|----|------|
| 问题 | 展平丢失 nested dict 导致 Tier1 渲染空 |
| 现状 | `rule_item_flatten` 对 dict key 逐条建 Item，`payload` 存数值 |
| 目标 | `body` 人类可读；`payload` 含 min/max/unit |
| 验收 | loader 渲染 hook_coverage_rate 等约束非空 |
| 代码 | `rule_item_flatten.py` quantitative 分支 |

### C3. ThemeTemplate.params 兼容（PDF #3）

| 项 | 内容 |
|----|------|
| 问题 | 移除 params 后 creation/delivery 读失败 |
| 目标 | 原子子表 + `params` 作 cache；读路径先 aggregate 再 fallback params |
| 验收 | submit + theme 选择回归 |
| 文档 | [13-CATALOG-ATOMIC-SPEC.md](./13-CATALOG-ATOMIC-SPEC.md) |

### C4. AgentSkillSection 单一 SSOT（PDF #4）

| 项 | 内容 |
|----|------|
| 问题 | content 与 section 双写不同步 |
| 目标 | 写 Section → sync → content；Admin 禁直接改 content |
| 验收 | API content 与 sections 拼接一致 |
| 文档 | [12-AGENT-SKILL-DEFINITION-SPEC.md](./12-AGENT-SKILL-DEFINITION-SPEC.md) |

---

## MEDIUM

### M1. Tier4 node 上下文（PDF #5）

Fusion 按 node 熔断 → 改为 **Agent 级 compliance Knowledge binding**；Tier4 Item 全局 scope 全 Agent 共享，特殊 Agent 额外 binding。

### M2. ThemeCharacterArchetype fit_genres（PDF #6）

避免 JSON 列表与 FK 重复；跨题材原型用独立 `CharacterArchetype` 主表 + M2M。

### M3. is_active / apply_count（PDF #7–8）

| 表 | 字段 |
|----|------|
| SkillRuleItem | apply_count ✓ |
| HookLibrary | use_count ✓ |
| 新 Catalog 原子表 | is_active, use_count 必选 |

### M4. SkillRuleConfig.content 去留（PDF #9）

`content_source`: json | atomic | hybrid；hybrid 时定期校验 Item 与 content hash。

### M5. section → 渲染映射（PDF #10）

不建 40+ Model；用 `rule_key` + `section` + `rule_item_flatten` 注册表；loader 只读 Item.body。

---

## MINOR

| # | 问题 | 修复 |
|---|------|------|
| 11 | emotion_value 整数 | ThemeEmotionCurve 用 SmallInteger 足够；若需小数改 Decimal |
| 12 | Decimal 精度 | 金额/比率字段统一 DecimalField |
| 13 | releasePassScore vs previewPassScore | SkillConfigEntry 分键或 payload 双字段 |
| 14 | 迁移无回滚 | [20-MIGRATION-RUNBOOK.md](./20-MIGRATION-RUNBOOK.md) |
| 15 | 缺数据迁移脚本 | flatten 命令 + 数据 migration 模板 |
| 16 | Tier3 Gate 命名 | Item title 区分 condition vs detail |
| 17 | ThemeHookType vs HookLibrary | 文档分层说明 ✓ |
| 18 | JSONField default=list | 用 `default=dict` 或 callable lambda |
| 19 | Admin Inline | SkillRuleConfigAdmin inlines Item |
| 20 | cross-reference | Item.payload.related_rule_ids: string[] |

---

## 验收总表

```bash
pytest backend/apps/skill/tests/rules/test_skill_rule_item.py -q
pytest backend/apps/creation/tests/test_independent_agent_runtime.py -q
```

## 旧逻辑删除

修复项中涉及 Fusion renderer 的代码路径在 [02-LEGACY-REMOVAL-PLAN.md](./02-LEGACY-REMOVAL-PLAN.md) Phase 3 一并移除。
