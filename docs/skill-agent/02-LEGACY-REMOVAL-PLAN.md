# Legacy / Fusion 删除计划

> **状态（2026-06-22 更新）**：已完成 Drama Skills v3.0 迁移。旧 brief/structure/character/outline/script/review/score agent 已全面替换为 drama.* 36角色体系。剩余待清理为 workflow/fusion/ 兼容层（中优先级，可分阶段进行）。

---

## 1. 范围

### 1.1 已删除（2026-06 记录）

见 `backend/apps/creation/legacy/README.md`：

- `apps/creation/orchestration/`
- `apps/creation/engine/`
- `apps/creation/step_mode.py`
- `apps/creation/workspace/workspace_service.py`（旧 payload）
- Admin orchestration / main-chain 路由

### 1.2 待删除（本计划）

| 模块 | 路径 | 说明 |
|------|------|------|
| Fusion Prompt | `backend/apps/workflow/fusion/prompt_builder.py` | 仅 Fusion 链使用 |
| Fusion 运行时桥接 | `backend/apps/workflow/skill_bridge.py` | 转调旧 skill invoker |
| Workflow 调度 | `backend/apps/workflow/workflow_scheduler.py`, `orchestration_adapter.py` | 自动节点推进 |
| Workflow tasks | `backend/apps/workflow/tasks.py` 中 fusion 分支 | Celery 旧链 |
| Workflow API | `backend/apps/workflow/api.py` 中非只读入口 | 评估后删 |
| Fusion SSOT Catalog | `workflow/fusion/ssot_catalog.py` | **已迁出** → `skill/config/portal/creation_catalog.py`（兼容层保留） |
| 旧节点 UI | `frontend/src/components/creation/workspace/*SkillPanel.jsx` | 若仅服务 7 节点工作台 |
| 文件 runner | `backend/apps/agent/runtime.py` 中 `importlib` 动态加载 runner_path | 改用 DB Agent |

### 1.3 保留（不删表/不删历史数据）

- `ProjectFusionArtifact` — 独立 Agent 仍使用
- `AgentExecutionRun` — 运行审计
- `SkillRuleConfig` / `SkillRuleItem` — SSOT
- Tier3 `scope_key=node-*` **数据** — 改绑定方式，不删行

---

## 2. 分阶段删除

### Phase 0：标记与流量切断

- [ ] 确认 C 端无入口调用 `/api/workflow/` 自动跑链（grep + 前端路由）
- [ ] `Project.pipeline_mode` 新项默认 `workspace`（已满足则跳过）
- [ ] 在 Fusion 模块顶加 `DeprecationWarning` 日志

### Phase 1：测试覆盖等价能力

| Legacy 能力 | 独立 Agent 等价 |
|-------------|-----------------|
| node-1 brief | `project_brief` Agent / submit seed |
| node-3 character | `character_bible` Agent |
| node-4 outline | `series_outline` Agent |
| node-5 script | `episode_scripts` Agent |
| node-6 review | `review_report` Agent |
| polish | `polish_log` + `polish_apply.py` |

补充集成测试：`backend/apps/creation/tests/test_independent_agent_runtime.py` 扩展 artifact 全链路。

### Phase 2：删路由与前端

- [ ] 移除 Admin Fusion 配置页、旧 Skill 工作台 Tab
- [ ] 移除 frontend 中 `generate_skill(node_index=…)` 调用（若仍存在）
- [ ] 文档指向 [CREATION-BUSINESS-ARCHITECTURE.md](../CREATION-BUSINESS-ARCHITECTURE.md)

### Phase 3：删后端代码

- [ ] 删除 `workflow/fusion/` 目录（保留被独立 Agent 引用的纯函数则迁到 `agent_runtime/`）
- [ ] 删除 `skill_bridge`, `orchestration_adapter`, `workflow_scheduler` 运行时调用
- [ ] 删除 management commands：`import_fusion_ssot`, `fusion_check`
- [ ] 清理 `agent/runtime.py` 文件 path runner

### Phase 4：数据归档

- 历史 Project 若 `pipeline_mode=legacy`：只读展示，禁止新 run
- 不执行 DROP TABLE

---

## 3. Tier3 node-* 规则迁移

旧 Fusion 按 `node_id` 加载 Tier3；新架构：

1. 为每个 Agent 增加 `AgentKnowledgeBinding`，`knowledge_id` 指向 flatten 后的 node 规则 Item 集合；或
2. 在 `SkillRuleLoader` 增加 `agent_id → tier3 scope_key` 映射表（DB 配置项 `SkillConfigEntry`）。

**禁止**：运行时硬编码 `node-5-script` 字符串 scattered 在 creation 模块。

---

## 4. 验收清单

```bash
# 应无引用（删除 Phase 3 后）
rg "FusionPromptBuilder|step_mode|workflow_engine" ScriptForge/backend --glob "!**/.idea/**"

# 主链测试通过
pytest backend/apps/creation/tests/test_independent_agent_runtime.py -q
```

---

## 5. 风险与回滚

| 风险 | 缓解 |
|------|------|
| 仍有用户走旧 URL | Phase 0 流量监控 + 404 友好提示 |
| 规则仅存在于 Fusion loader | 先完成 SkillRuleItem flatten + Knowledge 绑定 |
| 回滚 | Git revert Phase 3；DB 无 schema 回滚需求 |

---

## 6. 关联文档

- [00-MASTER-ARCHITECTURE.md](./00-MASTER-ARCHITECTURE.md)
- [11-SKILL-RULE-ITEM-SPEC.md](./11-SKILL-RULE-ITEM-SPEC.md)
- [20-MIGRATION-RUNBOOK.md](./20-MIGRATION-RUNBOOK.md)
