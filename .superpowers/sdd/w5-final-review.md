# ScriptForge V3 W5 终审报告 — 系统 / 模型 / 日志

> **审查范围：** 未提交工作区（只读，未 mutate git）  
> **计划：** `docs/superpowers/plans/2026-07-23-drama-website-v3-w5-system-models-logs.md`  
> **基线：** `docs/superpowers/baselines/2026-07-23-w5-system-models-logs-acceptance.md`  
> **设计验收：** `docs/superpowers/specs/2026-07-22-drama-website-v3-design.md` §8 项 4–6  
> **审查日：** 2026-07-23

## 审查方法

- 对照计划与基线逐项核对 API / 模型 / 编排 / 前端三页
- 约束 grep：`v6_runtime|v6_workbench|v6_control_plane`（orchestrator / skills_bridge / api/v3 / tasks_v3）→ **0 匹配**
- 独立机跑 W5 专项套件（非全量 178 回归）：
  - 后端 34 tests（system_config / system_api / models_api / provider_test / logs_api）→ **OK**
  - 前端 19 tests（SystemPage / ModelsPage / LogsPage）→ **OK**

---

## Strengths

1. **架构对齐计划**：`V3SystemConfigRevision` + `resolve_system_config()` / `save_system_overlay()` 分层清晰；foundation presets ⊕ overlay 语义与 Task 2 一致；不可变修订 + `select_for_update` 递增 revision 正确。
2. **模型层复用而非分叉**：`V3ModelsService` 包装 `LlmConfigService` + `secret_crypto`，响应白名单字段且显式 `pop("api_key")`；`resolve_for_role()` 在 executor 默认 LLM 路径生效，映射优先于 active provider 有单测覆盖。
3. **LLM 埋点设计合理**：`LlmCallContext` 扩展 `v3_command_run_id` / `v3_project_id`；executor 在 LLM 调用前 `llm_call_scope(...)`；`LlmCallLogService.record` 从 ContextVar 回填 FK，生成路径 `test_generate_links_llm_call_to_v3_run` 断言 prompt/response 可经 run 追溯。
4. **系统配置注入到位**：`_build_prompt` 对 `score_quality` / `check_compliance` 注入 `system_config` / 顶层 `scoring_preset` / `target_platform`；`test_v3_quality_executor` 有 overlay 变更后 prompt 断言。
5. **试连同步、可 mock**：`test_model_provider` 归入 `SYNC_PROVIDER_TEST_COMMANDS`；`provider_test` 用 `requests.get` + `@patch`；成功/失败均写 `CONNECTIVITY_TEST` 且响应/日志不含 api_key 明文。
6. **创作者 UI 产品化**：三页均为完整表单/列表/抽屉，中文标签；ModelsPage 密钥 write-only、编辑空串不覆盖；LogsPage 对 `operation.*` / kebab-case 配方型 command_type 脱敏，高级折叠才展示产品 `command_type` 枚举。
7. **约束遵守**：新路径无 v6 引用；无新增 npm/chart 依赖；API Key 脱敏有专门测例。

---

## Critical

**0 项**

未发现阻塞 W6 的安全红线或核心功能缺失：api_key 不回传、v6 未引入、W5 专项测试全绿、生成→run→call 主链路可追溯。

---

## Important

**3 项**

| # | 问题 | 风险 | 建议 |
|---|------|------|------|
| I1 | **试连日志未挂 `v3_command_run`**：`provider_test._record_log` 未包 `llm_call_scope`；`run_test_model_provider_command` 虽创建 run，但 run 详情 `calls` 为空 | §8.5「从项目动作追到 IO」在 **试连** 路径不完整；LogsPage 打开试连 run 看不到 CONNECTIVITY_TEST call | W6 前或 W6 首 task：试连时在 `_record_log` 或 command 入口注入 `v3_command_run_id` |
| I2 | **LogsPage 展开 prompt 暴露 `recipe_id`**：executor `_build_prompt` 将 kebab-case `recipe_id`（如 `score-script`）写入 user_prompt JSON；LogsPage `CallPromptPanel` 原样展示 | 与 §8.8 / 计划「创作者 UI 禁止配方 ID」存在灰区（command_type 已脱敏，prompt 内未脱敏） | 生成 prompt 时对创作者可见日志 strip `recipe_id`，或 LogsPage 渲染前 redact |
| I3 | **System overlay PUT 为整包替换**：`save_system_overlay` 存 `cleaned` 而非与上一 revision merge；二次 PUT 仅 `{scoring_preset}` 会丢失 `target_platform` overlay | API 误用导致 effective 回退；UI 因每次提交完整 overlay 暂安全 | OpenAPI/前端文档强调「每次 PUT 须提交完整 overlay」；或 W6 改为 merge 语义 |

---

## Minor

**5 项**

| # | 说明 |
|---|------|
| M1 | 系统配置全局、任意登录用户可 PUT（计划 intentional；多租户时需 W6+ 加角色） |
| M2 | `prepare_delivery` 未注入 `system_config`（score/compliance 已覆盖；交付路径可对称扩展） |
| M3 | LogsPage 固定 `limit=20`、无翻页控件 |
| M4 | OpenAPI 未列 `created_after` / `created_before`，实现已支持 |
| M5 | 无 run/project FK 的 CONNECTIVITY_TEST 记录无法经 `/logs/calls/{id}` 访问（owner 校验 404）— 与 I1 同源 |

---

## Spec Checklist §8.4–8.6

| Spec §8 | 要求摘要 | 证据 | 结论 |
|---------|----------|------|------|
| **§8.4 模型** | 可配置供应商与角色映射并试连成功 | `GET/POST/PATCH/DELETE …/models/providers/`；`activate`；`GET/PUT …/role-mappings/`；`POST …/test/` + 同步 `test_model_provider`；mock HTTP；api_key 加密且响应仅 `api_key_set` | **通过** |
| **§8.5 日志** | 任意一次生成可从项目动作追到输入/输出 | executor `llm_call_scope` → `DramaLlmCallLog.v3_command_run` FK；`GET /logs/runs/`、`…/runs/{id}/`、`…/calls/{id}/`；owner 隔离；`test_v3_logs_api.test_generate_links_llm_call_to_v3_run` | **通过**（试连子路径见 I1） |
| **§8.6 系统配置** | 改平台/门禁预设后后续运行读到新配置 | `V3SystemConfigRevision`；`GET/PUT /system/config/`；`resolve_system_config()`；score/compliance prompt 注入；SystemPage 读写 | **通过** |

**关联 §8.8（页面无 operation ID）：** 列表/标题层 `commandTypeLabel` 脱敏 `operation.*` 与 kebab-case 内部 ID；Vitest 覆盖。prompt 内 `recipe_id` 见 I2。

---

## 约束合规

| 约束 | 结果 |
|------|------|
| 无 `v6_*` | grep 0 匹配 |
| 无 api_key 泄漏 | models/logs/provider 测例 + serialize 白名单 |
| 创作者 UI 无 `operation.*` | LogsPage 脱敏 + 测例 |
| mock LLM/HTTP | 试连 `@patch(requests.get)`；生成 mock llm_call |
| 无新依赖 | frontend package 无 chart 等新库 |

---

## Verdict

### Ready for W6? **Yes**

W5 三件套（系统配置 revision+注入、模型 CRUD/映射/试连、日志挂 V3CommandRun + 三页 UI）满足计划验收与 §8.4–8.6。**Critical: 0，Important: 3**；Important 均为已知或可延至 W6 首迭代的追溯/UX 缺口，不阻断进入 W6（套餐壳 + 删旧 API/旧页）。

**建议在 W6 计划首 task 纳入 I1（试连 call 挂 run）与 I2（prompt 配方 ID 脱敏）**，避免日志页与 §8.8 长期不一致。

---

审查人：Senior Code Reviewer（只读终审，2026-07-23）
