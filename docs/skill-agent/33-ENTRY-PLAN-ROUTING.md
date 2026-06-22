# 创作入口 Plan 路由

---

## 1. 目标

按创作入口推荐 Agent 顺序与默认参数；**非 LLM** 动态 plan（PDF 借鉴 #2 简化版）。

## 2. 入口枚举

来自 `CreationFormOverrideConfig.overrides.creationEntries`：

| key | 说明 |
|-----|------|
| from-scratch | 从零创作 |
| from-outline | 已有大纲 |
| from-reference | 参考改编 |
| ip-sequel | IP 续作 |
| novel-adaptation | 小说改编 |

Project 字段：`creation_entry`（或 brief 内 entry key）。

## 3. Plan 配置表（已实现）

`SkillConfigEntry` key=`creation-entry-plans` + `entry_plan.py`；未知 agent_id 打 warn 日志。

```json
{
  "from-scratch": {
    "recommended_agents": ["structure", "character", "outline", "episode_scripts", "review"],
    "hidden_agents": [],
    "default_params": {}
  },
  "from-outline": {
    "recommended_agents": ["character", "episode_scripts", "review"],
    "hidden_agents": ["structure", "outline"]
  },
  "novel-adaptation": {
    "recommended_agents": ["episode_scripts", "review"],
    "hidden_agents": ["structure", "outline", "character"]
  }
}
```

agent_id 使用 `AgentDefinition.agent_id` 实际值。

## 4. 与 workspace 集成

`build_independent_workspace(project)`：

1. 读 `creation_entry` → plan
2. `recommended_agents` → UI 高亮/排序（`workspace_order` 二次排序）
3. `hidden_agents` → 不展示或折叠
4. `can_run` 仍由 **input_contract** 决定，Plan 不跳过依赖

## 5. Prompt 提示（已有雏形）

独立 Agent 可在 Knowledge 或 prompt 模板按 entry 注入不同 hint（原 `_ENTRY_PROMPT_HINTS` 逻辑），迁到 DB Knowledge 条目，`match_*` 过滤 creation_entry。

## 6. 与 billing

Plan 只影响 UI 推荐，**不**自动跑链；每次 run 仍单独触发。submit 扣费不变。

## 7. Admin

Admin → 创作配置 → Entry Plan 编辑 JSON 或专用表。

## 8. 测试矩阵

| 类型 | 验收 |
|------|------|
| normal | from-outline workspace 隐藏 structure |
| boundary | 未知 entry fallback from-scratch plan |
| error | plan 引用不存在 agent_id 时日志 warn |
| permission | Plan 配置仅 staff |

## 9. 旧逻辑删除

- `step_mode` 固定 1→7 节点映射
- `workflow_engine downstream_map` TODO — 不实现 LLM plan，用本配置表

参考：[02-LEGACY-REMOVAL-PLAN.md](./02-LEGACY-REMOVAL-PLAN.md)、[CREATION-BUSINESS-ARCHITECTURE.md](../CREATION-BUSINESS-ARCHITECTURE.md)。
