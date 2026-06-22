# SkillRuleItem 规范

> **状态**：已实现（`SkillRuleItem` + flatten 命令 + Admin Inline + active 约束）。

将 `SkillRuleConfig.content` 大 JSON 拆为可独立运营、审批、统计的原子条目；运行时优先读 Item。

## 2. 数据模型

文件：`backend/apps/skill/models.py` — `SkillRuleItem`

| 字段 | 类型 | 说明 |
|------|------|------|
| `rule_key` | varchar(256) | 全站 stable id，如 `t1.global.writing-prohibitions.no-open-ending` |
| `config` | FK → SkillRuleConfig | 来源配置包，可空 |
| `tier` | 1–4 | 层级 |
| `scope_type` | global / genre / node | 作用范围 |
| `scope_key` | varchar | 题材 code 或 node id（Tier3 遗留，改绑 Agent 时仍可用作过滤键） |
| `section` | varchar | 如 `writing_prohibitions`, `philosophy` |
| `item_type` | meta / rule | meta 为分区说明，默认 prompt 排除 |
| `title` | varchar | 短标题 |
| `body` | text | **渲染进 Prompt 的正文** |
| `payload` | JSON | 结构化附加（数值约束、嵌套字段） |
| `priority`, `sort_order` | int | 排序 |
| `version_tag` | varchar | 版本标签 |
| `status` | draft / active / archived | 生命周期 |
| `apply_count`, `last_applied_at` | 统计 | Loader 引用后递增 |

### 2.1 唯一约束（PDF 问题 #1 修复）

```python
UniqueConstraint(
    fields=["rule_key"],
    condition=Q(status="active"),
    name="skill_rule_item_active_key_uniq",
)
```

允许多条 **draft/archived** 同 `rule_key`；approve 时将旧 active 归档。

**禁止** `(tier, scope_type, scope_key, section)` 全局 unique_together — 会破坏 evolve_audit 多 draft。

## 3. rule_key 命名规范

格式：`t{tier}.{scope_slug}.{section_slug}.{path_slug}`

生成：`rule_item_flatten._build_rule_key()` — scope_slug 对 global 为 `global`，genre 为 `family-revenge` 等。

示例：

```
t1.global.quantitative-constraints.hook-coverage-rate
t2.family-revenge.requirements.emotion-peak
t3.node-5-script.gate-rules.check-01
```

## 4. Flatten 映射

实现：`backend/apps/skill/skills/rule_item_flatten.py`

### 4.1 跳过整包 section

`SKIP_SECTIONS`：`tier_full`, `tier1-iron-rules`, `tier2-genre-rules`, `tier3-workflow-rules`, `tier4-compliance-rules`, `skill-rules-index`, `skill-thresholds` 等 — 已有按 section 拆分的 Config 时不再二次 flatten。

### 4.2 列表字段 → 多条 Item

`LIST_FIELD_KEYS`：`requirements`, `prohibitions`, `gate_conditions`, `forbidden_phrases`, `p0_triggered` 等 — 数组每个元素一行。

### 4.3 量化约束 nested dict

`quantitative_constraints` 每个 key 一行 Item，`payload` 存 `{min, max, unit, numeric_value}`（见 [15-DATA-INTEGRITY-FIXES.md](./15-DATA-INTEGRITY-FIXES.md) 嵌套展平）。

### 4.4 触发 flatten

```python
SkillRuleItemService.flatten_from_configs(overwrite=True)
```

Console API：`POST /api/console/skills/rule-items/flatten/`（见 `rule_item_views.py`）。

## 5. 审批流

```
draft (evolve_audit / admin / file_import)
  → approve_item(item_id) → active
  → 同 rule_key 旧 active → archived
```

`SkillRuleItem.approve()` / `SkillRuleItemService.approve_item()` 与 Config 包 `approve()` 语义一致。

## 6. 运行时加载

`SkillRuleLoader._items_for_prompt(node_id, genre, tiers, sections)`：

1. 过滤 `status=active`, `item_type=rule`
2. Tier1/4：仅 `scope_type=global`
3. Tier2：`scope_key` 空或匹配 `genre`
4. Tier3：`scope_key` 空或匹配 `node_id`（独立 Agent 阶段改为 agent 映射表）

渲染：`_render_items()` → `[rule_key]\n{body}` 拼接。

引用统计：`SkillRuleItemService.record_apply(ids)` 更新 `apply_count`。

## 7. Admin / API

| 入口 | 路径 |
|------|------|
| Django Admin | `SkillRuleItemAdmin` — `backend/apps/skill/admin.py` |
| Console 列表 | `SkillRuleItemListView` |
| Console 审批 | `SkillRuleItemApproveView` |
| 前端 | `frontend/src/pages/Admin/tier-rules/SkillRulesPanel.jsx` |

## 8. 迁移

1. `import_skill_rules_to_db` → 写入 Config
2. `flatten_from_configs` → 写入 Item draft
3. 运营 approve 或批量 activate
4. 验证 loader 测试：`test_skill_rule_item.py`

## 9. 测试矩阵

| 类型 | 用例 | 文件 |
|------|------|------|
| normal | flatten philosophy section 产生 meta+rule | `test_skill_rule_item.py` |
| boundary | genre 过滤只加载匹配 scope_key | `SkillRuleItemLoaderTests` |
| error | 重复 approve 不违反 unique | approve 测试 |
| permission | 非 staff 不可 flatten | API 403 |

## 10. 旧逻辑删除

- Fusion `SkillRuleLoader.build_full_system_prompt()` 作为主链 — 删除
- Tier3 硬编码 node 顺序 — 删除；Item 数据保留

参考：[02-LEGACY-REMOVAL-PLAN.md](./02-LEGACY-REMOVAL-PLAN.md)。
