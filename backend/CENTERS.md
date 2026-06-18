# ScriptForge 十大中心架构

业务代码按 **10 个中心** 归类。C 端主链路为 **独立 Agent 工作台**（`creation/agent_runtime/`）。

## 中心一览

| 中心 | 职责 | Django App / 包路径 |
|------|------|---------------------|
| **流程中心** | Fusion Pack/Node、Schema、创作入口 catalog（非执行） | `workflow/` |
| **Agent 中心** | 独立 Agent 定义、Prompt、Knowledge、LLM 路由 | `agent/` |
| **创作中心** | 项目、产物、独立 Agent 工作台、分享下载 | `creation/`（`agent_runtime/`） |
| **技能中心** | Tier1–4 写作规则（原子能力） | `skill/skills/` |
| **配置中心** | 创作表单、题材/参考库、hooks、系统 KV | `skill/config/portal/` |
| **模型中心** | Provider、模型目录、Chat、全局 LLM 设置 | `skill/llm/` |
| **用户中心** | 账号、Profile、会员套餐权益 | `users/`、`membership/` |
| **监控中心** | 审计日志、`AgentExecutionRun`、LLM 用量 | `monitoring/`、`creation/monitoring/` |
| **商业中心** | 站点币、扣费、订单支付、充值定价 | `billing/`、`orders/` |

**API 网关**（非业务中心）：`portal/`（C 端）、`console/`（后台）、`common/`（横切工具）。

> **Legacy 已下线（2026-06）**：`orchestration/`、`WorkflowEngine` 执行链、Admin `main-chain` / `orchestration` API、batch 批量创作均已删除。运行监察见 **Agent 运行记录**。

## 数据流（现行）

```
用户请求 → 创作中心 submit
         → 独立 Agent 工作台（手动 run）
         → AgentExecutionRun 审计 + ProjectFusionArtifact 落库
         → 商业中心扣费 + 监控中心日志
```

## Admin API 前缀

| 中心 | 前缀 |
|------|------|
| Agent 配置 / 运行记录 | `/api/admin/agent/` |
| 创作项目运营 | `/api/admin/creation/projects/` |
| 配置中心 | `/api/admin/portal/` |
| 技能规则 | `/api/admin/skills/rules/` |
| 模型 | `/api/admin/model/llm/` |

已下线：`/api/admin/orchestration/`、`/api/admin/main-chain/`、`/api/admin/workflow/`（执行类）。

## 常用 import

```python
from apps.agent.definition_service import AgentDefinitionService
from apps.creation.agent_runtime.independent_service import IndependentAgentService
from apps.creation.agent_runtime.workspace import build_workspace_catalog
from apps.workflow.fusion import get_artifact_registry
from apps.agent.routes import AgentLlmRouteService
```
