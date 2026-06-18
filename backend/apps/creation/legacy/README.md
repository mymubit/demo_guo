# Legacy 模块索引（已删除）

以下模块已于 2026-06 Legacy 完整下线中删除，勿再引用：

| 原路径 | 说明 |
|--------|------|
| `apps/creation/orchestration/` | 子技能编排 runner |
| `apps/creation/engine/` | 旧 7 节点 Python 引擎 |
| `apps/creation/step_mode.py` | 分步流水线 |
| `apps/creation/workspace/workspace_service.py` | 旧工作台 payload |
| `apps/workflow/workflow_engine.py` | 已 stub，实例化抛错 |
| Admin `orchestration/` / `main-chain/` | 已删路由与前端 |

**当前主链路**：`submission` → `IndependentAgentWorkspace` → `run_independent_agent` → `ProjectFusionArtifact`

迁移出的工具：
- `agent_runtime/episode_merge.py`
- `polish_apply.py`
- `character_gate.py`
- `workspace/artifact_keys.py`
- `workspace/verify_summary.py`
- `pipeline_result.py`
