# Legacy 创作编排（非 C 端主路径）

本目录说明仍保留、但**不再用于独立 Agent 工作台**的代码入口。

## 当前主链路

`submit` → `project_brief` → `IndependentAgentWorkspace` → `run_independent_agent` → `ProjectFusionArtifact`

## 仍保留的 Legacy 入口

| 入口 | 位置 | 说明 |
|------|------|------|
| `run_creation_pipeline` | `apps/creation/tasks.py` | 旧 7 节点自动流水线 |
| `run_creation_step` | `apps/creation/tasks.py` | 旧工作台单步执行 |
| `WorkflowEngine` | `apps/workflow/workflow_engine.py` | Fusion 编排引擎 |
| `invoke_workspace_agent` | `apps/creation/orchestration/workspace_agent.py` | 子技能编排入口 |
| `apps/creation/orchestration/*` | 各 Agent runner | 供旧 pipeline / 管理工具调用 |

**请勿**在新功能或 Portal C 端路径中直接 import 上述模块。
