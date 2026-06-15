# ScriptForge 十大中心架构

业务代码按 **10 个中心** 归类。Agent 中心是调度中心与技能中心之间的 **组合绑定层**；流程中心承载声明式流水线定义。

## 中心一览

| 中心 | 职责 | Django App / 包路径 |
|------|------|---------------------|
| **流程中心** | 主链步骤图、Fusion Pack/Node、Schema、runner/币价/确认 | `workflow/` |
| **Agent 中心** | 技能注册表、步骤→Agent 绑定、sub_skills 链、Agent LLM 路由、质检策略 | `agent/` |
| **调度中心** | 运行时选步、加锁、触发执行、执行轨迹 | `creation/orchestration/` |
| **技能中心** | Tier1–4 写作规则（原子能力） | `skill/skills/` |
| **配置中心** | 创作表单、题材/参考库、hooks、系统 KV | `skill/config/portal/` |
| **模型中心** | Provider、模型目录、Chat、全局 LLM 设置 | `skill/llm/` |
| **创作中心** | 项目、作品、产物、Workspace、分享下载 | `creation/`（根层服务） |
| **用户中心** | 账号、Profile、会员套餐权益 | `users/`、`membership/` |
| **监控中心** | 审计日志、执行日志、LLM 用量、运营统计 | `security/`、`creation/execution_*` |
| **商业中心** | 站点币、扣费、订单支付、充值定价 | `billing/`、`orders/` |

**API 网关**（非业务中心）：`portal/`（C 端）、`console/`（后台）、`common/`（横切工具）。

## 数据流

```
用户请求
   ↓
调度中心 ──读──→ 流程中心（步骤顺序/币价/runner 定义）
   │              Agent 中心（步骤绑定的技能链、Prompt、子技能）
   │              技能中心（写作规则）
   │              模型中心（Provider 路由）
   ↓
子技能实时编排
   ↓
创作中心（产物落库） + 商业中心（扣费） + 监控中心（日志）
```

## 中心边界

| 中心 | 管什么 | 不管什么 |
|------|--------|----------|
| **流程中心** | 第几步、顺序、启用、币价、runner 类型、Fusion Schema | sub_skills、Prompt、LLM |
| **Agent 中心** | 主链 Agent 定义、workspace 映射、后处理链、步骤绑定 | 步骤顺序（流程中心）、原子规则（技能中心） |
| **调度中心** | 何时跑、锁、重试、轨迹 | Agent/Pipeline 配置写入 |

## 目录映射

### workflow/

```
workflow/
├── models.py              # FusionPipelinePack/Node, FusionJsonSchema
├── pipeline_store.py      # FusionPipelineDbService
├── step_admin.py          # PipelineStepAdminService
├── fusion/                # Schema、Artifact、readiness
└── bootstrap/             # workflow_disk 等种子
```

### agent/

```
agent/
├── models.py              # AgentRegistryConfig, AgentLlmRouteConfig, ReviewScoringConfig
├── registry.py            # AgentRegistryConfigService
├── binding.py             # 节点→Agent 绑定
├── catalog.py             # Portal Agent 目录
├── runtime.py             # 运行时 registry 缓存读
├── routes.py              # Agent LLM 路由
└── bootstrap/             # tier1、agent_llm_routes 种子
```

### creation/

```
creation/
├── orchestration/         # 调度中心（纯运行时）
├── models.py / workspace_* / artifact_*  # 创作中心
└── engine/                # legacy，逐步废弃
```

### skill/（收窄）

```
skill/
├── skills/                # 技能中心 — 仅 loader + admin_service（规则）
├── config/portal/         # 配置中心
├── config/bootstrap/      # 非 workflow/agent 种子
└── llm/                   # 模型中心
```

## 常用 import

```python
# 流程
from apps.workflow.pipeline_store import FusionPipelineDbService
from apps.workflow.fusion.registry import FusionNodeRegistry

# Agent
from apps.agent.registry import AgentRegistryConfigService
from apps.agent.binding import agent_id_for_fusion_node
from apps.agent.catalog import portal_agent_catalog

# 调度
from apps.creation.orchestration.orchestrator import AgentOrchestrator

# 技能规则
from apps.skill.skills.loader import SkillRuleLoader

# 模型
from apps.skill.llm.chat import LlmService
from apps.agent.routes import AgentLlmRouteService
```

## API 术语

- **主链**：对外 **`agent_id`**（请求体 `skill_id` 为废弃别名）
- **子技能**：对外 **`skill_id`** / **`sub_skill_id`**（与 `SubSkillExecutionLog` 一致）
- 术语工具：`apps/common/agent_term.py`（主链）、`apps/common/skill_term.py`（子技能）
- 硬编码种子：`workflow/bootstrap/`、`agent/bootstrap/`、`skill/config/bootstrap/`

## Admin API 前缀

| 中心 | 前缀 |
|------|------|
| 主链工作室 | `/api/admin/main-chain/` |
| Agent | `/api/admin/agent/` |
| 调度监察 | `/api/admin/orchestration/` |
| Agent 目录 | `/api/admin/agent/catalog/` |
| 配置中心 | `/api/admin/portal/` |
| 技能规则 | `/api/admin/skills/rules/` |
| 模型 | `/api/admin/model/llm/` |

旧路径 `/api/admin/workflow/`、`/api/admin/pipeline/`、`/api/admin/fusion/`、`/api/admin/agents/`、`/api/admin/skill/` 已下线。请改用下表中心前缀。

### 旧路径迁移对照（Admin）

| 旧前缀 | 新前缀 |
|--------|--------|
| `/api/admin/workflow/`、`/pipeline/`、`/fusion/` | `/api/admin/main-chain/` |
| `/api/admin/agents/` | `/api/admin/orchestration/` |
| `/api/admin/skill/agent-registry/` | `/api/admin/agent/registry/` |
| `/api/admin/skill/llm/` | `/api/admin/model/llm/` |
| `/api/admin/skill/creation-form/`、`/themes/`、`/hooks/`、`/configs/` | `/api/admin/portal/` |
| `/api/admin/skill/rules/` | `/api/admin/skills/rules/` |

## 迁移阶段

- [x] Phase 1–4：目录重组与 skill_id 试验（已回退主链术语）
- [x] Phase 6：Admin API 前缀收敛 — `main-chain` / `orchestration` / `portal` / `skills`，旧 workflow/skill/agents 下线
