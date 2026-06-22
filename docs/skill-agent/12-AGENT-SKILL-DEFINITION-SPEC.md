# AgentSkillDefinition 规范

---

## 1. 目标

管理 Cursor/工具侧 SKILL.md SSOT；与 C 端 `AgentDefinition` 协同，避免双 SSOT 漂移。

## 2. 数据模型

`backend/apps/skill/models.py` — `AgentSkillDefinition`

| 字段 | 说明 |
|------|------|
| `skill_id` | 唯一标识，如 `creation.script` |
| `name`, `version` | 展示与 semver |
| `content` | 完整 Markdown（原 SKILL.md） |
| `skill_layer` | foundation / business / tool |
| `sub_category` | 人设/大纲/剧本/审核 等 |
| `lifecycle_status` | draft / active / gray / deprecated |
| `gray_weight` | 0–100 灰度权重 |
| `gray_traffic_salt` | 稳定分流盐 |
| `published_at`, `deprecated_at` | 生命周期时间 |
| `input_schema`, `output_schema` | JSON Schema |
| `system_hint` | System 片段 |
| `timeout_seconds`, `quota_cost`, `retry_policy`, `fallback_skill_id` | 执行策略 |
| `tags` | JSON 场景标签 |
| `source_file` | 迁移来源路径 |

## 3. 与 AgentDefinition 的主路径

| 场景 | 主 SSOT |
|------|---------|
| C 端用户点击运行 | `AgentDefinition` + `AgentPromptVersion` + Knowledge |
| Cursor Agent 拉定义 | `AgentSkillDefinition` API |
| 内容同步 | import 命令：`AgentSkillDefinition` → `AgentKnowledgeItem`（推荐） |

**实施约定**：C 端 `IndependentAgentService` **不直接**读取 `AgentSkillDefinition.content`；若需复用，通过 Knowledge binding 注入。

## 4. AgentSkillSection（已实现）

PDF 第六节：`content` 大字符串按 section 拆分。

表：`skill_agent_skill_section` — 见 `apps/skill/models_catalog.py`；`sync_content_from_sections()` 见 `apps/skill/skills/skill_section_sync.py`。

建议表结构：

| 字段 | 说明 |
|------|------|
| `skill` | FK AgentSkillDefinition |
| `section_key` | system_prompt / input_schema / quality_checklist / anti_patterns / examples |
| `section_content` | text |
| `section_schema_json` | schema 类 section 用 JSON |
| `sort_order`, `is_active` | 排序与启停 |

### 4.1 单一 SSOT（PDF 问题 #4）

- **写路径**：仅编辑 Section 表 → `sync_content_from_sections()` 生成 `content` 缓存字段
- **读路径（API）**：对外返回 `content`；内部编辑用 Section
- **禁止**：Admin 同时改 `content` 与 Section 且无同步

## 5. 灰度分流

条件：`lifecycle_status=gray`

```
bucket = hash(gray_traffic_salt + str(user_id)) % 100
命中 gray 版本 ⟺ bucket < gray_weight
```

同一 `skill_id` 可并存 active（全量）与 gray（实验）版本；解析时按 user_id 选一条。

详见 [22-VERSION-GRAY-RELEASE.md](./22-VERSION-GRAY-RELEASE.md)。

## 6. 生命周期

| 状态 | 行为 |
|------|------|
| draft | 仅 Admin/Console 可见 |
| active | 全量生效 |
| gray | 按权重分流 |
| deprecated | 拒绝新调用；历史 run 可读 |

## 7. Admin / API

- Admin：`SkillCenterPage`, `SkillDetailPanel`
- Console：`/api/console/skills/`（见 `test_portal_skills_api.py`）
- 导入：`python manage.py import_skills_to_db`

## 8. 迁移

```bash
python manage.py import_skills_to_db
python manage.py migrate_agent_skill_config  # 旧结构迁移
python manage.py import_agent_assets         # 资产校验
```

## 9. 测试矩阵

| 类型 | 验收 |
|------|------|
| normal | active skill API 返回 content + schemas |
| boundary | gray_weight=0 永不命中 gray 版 |
| error | deprecated skill 调用返回 404/业务码 |
| permission | 非 staff 不可改 lifecycle |

## 10. 旧逻辑删除

- 运行时读取磁盘 `.cursor/skills/**/SKILL.md` 作为 SSOT — 改为 DB
- Fusion skill_id 硬映射 — 删除

参考：[01-AGENT-SKILL-USER-LAYERS.md](./01-AGENT-SKILL-USER-LAYERS.md)。
