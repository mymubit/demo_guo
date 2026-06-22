# 数据迁移 Runbook

---

## 1. 目标

新环境/升级环境一次性导入 Skill/Agent SSOT；幂等、可回滚；**不含 Fusion 专用命令**。

## 2. 前置检查

| 项 | 命令/位置 |
|----|-----------|
| 数据库迁移 | `python manage.py migrate` |
| 加密 Key | `settings.SKILL_ENCRYPT_KEY`（32 字节或 SHA256 派生） |
| 资产根目录 | `settings.SCRIPT_FORGE_ASSET_ROOT` |
| LLM 配置 | 环境变量或 Admin 录入 `LlmProvider` |

## 3. 标准执行顺序

```bash
# 1. 基础 Catalog + 加密配置 + 题材/钩子
python manage.py init_skill_data

# 2. Tier JSON → SkillRuleConfig
python manage.py import_skill_rules_to_db
python manage.py import_tier_rules_to_db   # 补充导入（若 split）

# 3. Config → SkillRuleItem（Console 或 shell）
# SkillRuleItemService.flatten_from_configs(overwrite=False)

# 4. SKILL.md → AgentSkillDefinition
python manage.py import_skills_to_db

# 5. 硬编码 Python 常量 → DB
python manage.py migrate_hardcoded_configs_to_db
python manage.py migrate_hardcoded_hints
python manage.py migrate_system_hints_to_db

# 6. Agent 资产与独立 Agent 种子
python manage.py import_agent_assets
python manage.py seed_independent_agents

# 7. LLM 目录/定价（可选）
python manage.py setup_volcano_agent_llm
python manage.py sync_llm_official_pricing
python manage.py sync_volcano_endpoints
```

`init_skill_data` 内部调用 `apps.skill.config.portal.skill_settings.init_skill_data()`。

## 4. 不执行的命令（Legacy）

| 命令 | 原因 |
|------|------|
| `import_fusion_ssot` | Fusion SSOT，随 Fusion 删除 |
| `fusion_check` | Fusion 校验 |

## 5. content_source 语义（SkillRuleConfig）

| 值 | 含义 |
|----|------|
| `json` | 仅以 `content` JSON 为准 |
| `atomic` | 仅以 SkillRuleItem 为准 |
| `hybrid` | Item 优先，content 作 cache/回滚 |

目标态：Tier1–4 活跃规则为 `atomic` 或 `hybrid`。

## 6. 幂等与 overwrite

| 操作 | 策略 |
|------|------|
| import_skill_rules_to_db | 按 (tier, scope, section, status) upsert draft 或 skip |
| flatten | `overwrite=True` 重建 draft；False 仅补缺 |
| import_skills_to_db | 按 skill_id update content |
| seed_independent_agents | ensure_defaults 不覆盖 active prompt |

## 7. 回滚

| 层级 | 做法 |
|------|------|
| Item 错误 approve | 将 active 改 archived，恢复上一 archived 为 active |
| Config 错误 | 从 `status=archived` 行恢复 |
| 全量失败 | DB 快照恢复；**禁止**生产 hard reset |
| 代码回滚 | Git revert；DB 向前兼容 |

## 8. 验收 SQL（示例）

```sql
-- active Item 数量
SELECT tier, COUNT(*) FROM skill_rule_item WHERE status='active' GROUP BY tier;

-- 每 Agent 有 active prompt
SELECT d.agent_id FROM agent_definition d
LEFT JOIN agent_prompt_version p ON p.agent_id=d.id AND p.is_active
WHERE p.id IS NULL;
```

## 9. 测试矩阵

| 类型 | 验收 |
|------|------|
| normal | 空库跑完全序列后 workspace 有 Agent |
| boundary | 重复执行命令不 duplicate active rule_key |
| error | 缺 SKILL_ENCRYPT_KEY 时 import 失败有明确日志 |
| permission | migrate 仅 deploy 角色可执行 |

## 10. 旧逻辑删除

迁移完成后删除对磁盘 `references/tier*.json` 的运行时依赖；JSON 仅作 import 源保留在 asset 目录。

参考：[02-LEGACY-REMOVAL-PLAN.md](./02-LEGACY-REMOVAL-PLAN.md)、[11-SKILL-RULE-ITEM-SPEC.md](./11-SKILL-RULE-ITEM-SPEC.md)。
