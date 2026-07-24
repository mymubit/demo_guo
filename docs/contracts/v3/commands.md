# V3 产品命令字典

> 契约冻结（W0）— 产品 `command_type` 枚举与中文展示名。  
> 供 OpenAPI、`commands.ts` 及编排器入口引用。

| command_type | 中文名 | 模块 | 异步 | 需确认候选 |
|--------------|--------|------|------|------------|
| create_project | 创建项目 | 项目 | 否 | 否 |
| generate_topic_brief | 生成选题简报 | 选题 | 是 | 是 |
| confirm_topic_brief | 确认选题简报 | 选题 | 否 | 否 |
| generate_blueprint | 生成故事蓝图 | 蓝图 | 是 | 是 |
| confirm_blueprint | 确认故事蓝图 | 蓝图 | 否 | 否 |
| generate_episode_plan | 生成分集规划 | 分集 | 是 | 是 |
| confirm_episode_plan | 确认分集规划 | 分集 | 否 | 否 |
| revise_episode_plan | 局部修订分集 | 分集 | 是 | 是 |
| write_episode_batch | 分批写正文 | 正文 | 是 | 是 |
| confirm_script_candidate | 确认正文候选 | 正文 | 否 | 否 |
| score_quality | 质量评分 | 质检 | 是 | 否 |
| check_compliance | 合规审查 | 质检 | 是 | 否 |
| accept_findings | 接受质检问题 | 质检 | 否 | 否 |
| revise_from_findings | 按问题修订 | 质检 | 是 | 是 |
| prepare_delivery | 生成交付包 | 交付 | 是 | 否 |
| test_model_provider | 试连模型 | 模型 | 否 | 否 |

## 说明

内部 skills 配方 ID（如 `operation.create-project-brief`）只写在编排器映射表，不进本表「对用户」列。

### 质检 / 交付执行约定（W4）

| 约定 | 说明 |
|------|------|
| `accept_findings` | **同步**命令：无 LLM、无候选确认；直接 upsert `V3QualityFinding`（status=`accepted`） |
| `score_quality` / `check_compliance` | 异步 live；成功后报告直接 **committed**（supersede 旧版）；**无**独立 confirm 命令 |
| `prepare_delivery` | 异步 live；门禁通过后 `production_package` 直接 **committed**；**无**独立 confirm 命令 |
| `revise_from_findings` | 异步产出 `episode_scripts` 候选；确认沿用既有 `confirm_script_candidate` |

报告 payload 可含编排器附加字段 `_v3_meta.source_script_version`；正文升版后报告 `is_stale=true`。

### 模型试连约定（W5）

| 约定 | 说明 |
|------|------|
| `test_model_provider` | **同步 live**：对指定 `provider_id` 发最小连通性探测（mock HTTP 可测）；成功/失败均写 `CONNECTIVITY_TEST` 日志 |
| payload | `{ "provider_id": "<uuid>" }`；亦可走 REST `POST /models/providers/{id}/test/` |
| 异步 | **否**（快速反馈，避免排队噪音） |

供应商 CRUD / 角色映射 / 系统配置为 REST 资源，不进入本表。

### 模块覆盖（Spec §5）

| HTML 模块 | 本表 command | 备注 |
|-----------|--------------|------|
| 项目管理 | `create_project` | 归档/进度聚合为 REST 读操作，无独立 command |
| 选题定调 | `generate_topic_brief`、`confirm_topic_brief` | |
| 蓝图编辑 | `generate_blueprint`、`confirm_blueprint` | |
| 分集画布 | `generate_episode_plan`、`confirm_episode_plan`、`revise_episode_plan` | |
| 正文编辑 | `write_episode_batch`、`confirm_script_candidate` | |
| 质检中心 | `score_quality`、`check_compliance`、`accept_findings`、`revise_from_findings` | |
| 交付工具 | `prepare_delivery` | |
| 系统配置 | — | REST 资源（`/api/v3/system/`），非 command |
| 模型配置 | `test_model_provider` | 供应商/密钥/映射为 REST CRUD |
| 执行日志 | — | REST 只读（`/api/v3/logs/`），非 command |
| 套餐壳 | — | REST 只读（`/api/v3/billing/plans/`），无 command |
