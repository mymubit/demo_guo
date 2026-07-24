# V3 Phase-2：跨供应商 Failover + 用量/费用可观测 — 设计

> 日期：2026-07-23  
> 前置：V3 phase-1（W0–W6）已收口；见 `docs/superpowers/plans/2026-07-22-drama-website-v3.md`  
> 真相源补充：本文件；产品 IA 仍对齐 `drama-website-design`（新增 `/usage` 为 phase-2 扩展）

## 1. 背景与目标

phase-1 已具备单供应商角色映射、LLM call log、Logs/Models 页。W5/W6 明确延期了多 Key/failover 与成本图。

**目标：** 在不回退到 `v2`/`v6_runtime` 的前提下，交付：

1. **跨供应商主备 failover（F2）**：按角色映射的有序备选链，生成路径自动切换；每次尝试可审计。
2. **用量/费用可观测（K3）**：token + 估算费用 + ECharts；独立 **`/usage`** 页（U2）。

采用 **方案 2**：独立 `failover_policy` + `V3FailoverAttempt` 表 + **日汇总物化**（非前端全量拼装）。

## 2. 范围与非目标

### 2.1 范围内

| 项 | 说明 |
|----|------|
| 角色主备链 | `V3RoleModelMapping`：主 `provider` + 有序 `backup_provider_ids`（跨供应商） |
| Failover 运行时 | `failover_policy` + `LlmRouter`；接入生成路径 |
| 尝试审计 | `V3FailoverAttempt`；Logs run 详情只读展示 |
| 单价 | `V3ModelPrice`（provider/model → 输入/输出 元/1K tokens） |
| 日汇总 | `V3UsageDailyRollup`；Usage API 默认读 rollup |
| 前端 | Models 扩展主备编辑；新建 `/usage`；引入 ECharts（须在 plan 中钉版本与理由） |

### 2.2 明确不做

- 轨 A：Tiptap / Word / PDF
- 真实支付、订阅、配额门禁
- 加权路由、复杂熔断冷却（可预留字段，本期不做策略引擎）
- 多租户按 owner 隔离的「系统单价」权限拆分（沿用现有登录/管理员约定）
- 往已删除的 `v2_*` / `v6_runtime` / `v6_workbench` / `v6_control_plane` 加功能
- 创作者 UI 暴露 operation ID / recipe ID

## 3. 架构

### 3.1 组件

| 单元 | 职责 |
|------|------|
| `orchestrator/failover_policy.py` | 解析角色主备链；判断错误是否可切换；组装策略元数据 |
| `orchestrator/llm_router.py`（或 `services/llm_router.py`） | 按链调用 `LlmProvider.chat_completion`；写 attempt + 关联 call log |
| `V3FailoverAttempt` | 每次尝试一行 |
| `V3ModelPrice` | 单价配置 |
| `V3UsageDailyRollup` | 按日物化用量/费用 |
| `api/v3/usage_*` | 汇总查询；可选近窗 live |
| `api/v3/models_*` | 扩展 role-mapping 备选；单价 CRUD（可挂 `/models/prices/`） |
| `UsagePage` | `/usage`：筛选 + 表 + ECharts |
| `ModelsPage` | 主 + 备选排序；不承载成本图 |
| `LogsPage` | run 详情增加 failover 尝试列表 |

### 3.2 调用流

```
execute_generation / provider 试连（若适用）
  → failover_policy.resolve_chain(role)
  → LlmRouter.chat(...)
       for attempt in chain:
         写 FailoverAttempt(running)
         调 LlmProvider + 写 DramaLlmCallLog
         成功 → 标记 attempt succeeded；返回正文
         可切换失败 → 标记 failed_switchable；下一备选
         不可切换 → 标记 failed_terminal；中止
       链耗尽 → 抛错；run 失败摘要含「已尝试供应商」（中文）
  → 仅最终成功响应进入产物解析
  → 成功 call 触发当日 rollup 增量更新
```

### 3.3 用量流

- **写路径：** 成功（及可选失败）call log 落库后，同步或 Celery 增量更新 `V3UsageDailyRollup`（维度见 §4）。
- **读路径：** `GET /api/v3/usage/summary/` 默认读 rollup；`live=1` 时对近 N 小时直查 call log 合并展示（防图表滞后）。
- **费用：** `(prompt_tokens/1000)*price_in + (completion_tokens/1000)*price_out`；无单价则 `estimated_cost=null`，UI「未定价」。

## 4. 数据模型

### 4.1 扩展 `V3RoleModelMapping`

| 字段 | 类型 | 说明 |
|------|------|------|
| `provider` | FK | 主供应商（已有） |
| `backup_provider_ids` | JSON list[uuid] | 有序备选，跨供应商；默认 `[]` |
| temperature / max_tokens | 已有 | 对整条链生效（一期不按备选覆盖） |

约束：备选不得包含主 id；列表去重保序；引用必须存在且启用校验在写 API。

### 4.2 `V3FailoverAttempt`

| 字段 | 说明 |
|------|------|
| `id` | UUID |
| `v3_command_run` | FK，可空（试连可挂 run） |
| `v3_project` | FK，可空 |
| `owner` | FK User |
| `role_key` | 技能角色 |
| `provider` | FK |
| `attempt_index` | 从 0 起 |
| `status` | `succeeded` / `failed_switchable` / `failed_terminal` / `skipped` |
| `error_code` | 短码：`timeout` / `http_429` / … |
| `error_message` | 脱敏短文 |
| `llm_call_log` | FK null |
| `created_at` | |

### 4.3 `V3ModelPrice`

| 字段 | 说明 |
|------|------|
| `provider` | FK |
| `model_name` | 与 call log `model_name` 对齐 |
| `price_in_per_1k` | Decimal，元 |
| `price_out_per_1k` | Decimal，元 |
| `currency` | 默认 `CNY` |
| unique | `(provider, model_name)` |

### 4.4 `V3UsageDailyRollup`

维度：`date`（UTC 或项目约定 Asia/Shanghai，**实现须在 OpenAPI 写死一种**）、`owner_id`、`project_id`（可空）、`command_type`（可空）、`model_name`、`provider_id`（可空）。

度量：`prompt_tokens`、`completion_tokens`、`total_tokens`、`call_count`、`success_count`、`estimated_cost`（Decimal；仅已定价 call 计入，未定价不抬高累加值，另可用 `unpriced_call_count` 可选字段——**一期实现须带 `unpriced_call_count`** 以免静默丢数据）。

**时区：** rollup 的 `date` 统一为 **Asia/Shanghai** 日历日（在 OpenAPI `description` 写死）。

## 5. Failover 错误策略

**可切换（进入下一备选）：** 超时、连接失败、HTTP 401/403/408/429/5xx、供应商未启用/配置不全。

**不可切换（立即失败）：** 调用已成功后的业务错误（非 JSON、schema 失败等）。

**内容策略拒绝：** 一期若无法可靠识别，按可切换处理并记 `error_code`，避免误杀；后续可收紧。

试连（`test_model_provider`）：只测**指定** provider，**不走**备选链（避免误伤配置 UI 语义）。

## 6. API 契约（草案，W1/W2 冻结进 OpenAPI）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/PUT | `/api/v3/models/role-mappings/` | items 增加 `backup_provider_ids: string[]` |
| GET/PUT | `/api/v3/models/prices/` | 单价列表/批量更新 |
| GET | `/api/v3/usage/summary/` | query：`project_id`、`date_from`、`date_to`、`group_by`、`live` |
| GET | `/api/v3/logs/runs/{id}/` | `data` 增加 `failover_attempts: [...]` |

信封仍为 `{code,message,data}`。

## 7. 前端

- 导航新增 `/usage`（文案建议：「用量」，hint：「Token 与费用」），放在 Logs 与 System 之间或 Models 之后。
- `UsagePage`：日期/项目/命令筛选；汇总表；ECharts 趋势（按日 token/费用）与对比（按模型）。
- `ModelsPage`：每角色主下拉 + 备选有序列表（添加/上移/下移/删除）。
- `LogsPage`：详情区「切换尝试」列表（供应商名、结果、耗时）；禁止展示 operation/recipe ID。
- ECharts：仅 Usage 页按需动态 import；版本与引入理由写在实现 plan Global Constraints。

## 8. 测试与验收

### 8.1 测试要求

- 单测：链解析、可切换/不可切换、成功提前停止、链耗尽、rollup 增量、无单价 null 费用
- API 测：mapping 备选、prices、usage summary、run 详情 attempts
- 前端测：Models 备选编辑；Usage 有表+图容器；无 banned tokens
- 一律 mock HTTP；禁止真实外网

### 8.2 验收标准

1. 主挂备通：同一 `command_run` 有 ≥2 条 attempt，产物仍成功写入  
2. 链耗尽：run 失败且全部 attempt 已记录  
3. `/usage` 按筛选可见 token 与估算费用（含 ECharts）  
4. 无支付/配额；无 Tiptap；legacy grep 对 v2/v6 产品路径仍为 0  
5. 试连不误走备选链  

## 9. 里程碑

| 里程碑 | 交付 | 验收物 |
|--------|------|--------|
| **P2-W1** | 模型 + policy + router + FailoverAttempt；生成路径接入；Logs 展示 | 基线 + 机跑 |
| **P2-W2** | Models 主备 API/UI；单价；日 rollup；Usage API | 基线 + 机跑 |
| **P2-W3** | `/usage` + ECharts；全量回归 | §8 全勾选基线 |

执行方式：推荐 `superpowers:subagent-driven-development`；工作目录 `c:\Users\99193\Desktop\demo_guo`；**未明确要求不 git commit**。

## 10. 决策记录

| 决策点 | 选择 |
|--------|------|
| phase-2 主题 | 仅轨 C（A 延期） |
| 范围档 | C3 = failover + 成本可观测 |
| Failover | F2 跨供应商主备链 |
| 成本 UI | K3 token + 估算费用 + ECharts |
| 页面 | U2 新建 `/usage`；Models 只管映射 |
| 架构 | 方案 2（独立 attempt 表 + 日 rollup） |
