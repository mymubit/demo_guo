# W5 Final Review — Important 修复报告

> **日期：** 2026-07-23  
> **范围：** I1 / I2 / I3（`w5-final-review.md` Important ×3）  
> **约束：** 未 git commit

## Status

**Fixed — all 3 Important findings**

| # | 问题 | 状态 |
|---|------|------|
| I1 | 试连日志未挂 `v3_command_run` | ✅ Fixed |
| I2 | LogsPage 展开 prompt 暴露 `recipe_id` / `operation.*` | ✅ Fixed |
| I3 | System overlay PUT 整包替换 | ✅ Fixed |

---

## I1 — 试连日志挂 V3CommandRun

**根因：** `run_test_model_provider_command` 创建 run 后调用 `test_provider_connectivity`，但 `_record_log` → `LlmCallLogService.record` 未注入 `llm_call_scope`，`v3_command_run` FK 为空。

**修复：** 在 dispatcher 试连路径用 `llm_call_scope(v3_command_run_id=..., v3_project_id=..., purpose=CONNECTIVITY_TEST)` 包裹 `test_provider_connectivity`。

**文件：** `backend/apps/drama/orchestrator/provider_test.py`

**测试：**
- `test_test_model_provider_sync_success_writes_log` — 断言 `log.v3_command_run_id == run.id`
- `test_test_model_provider_http_failure_is_failed_with_zh` — 失败路径同样挂 run
- `test_dispatcher_connectivity_log_visible_on_run_detail` — `GET /logs/runs/{id}/` 返回 CONNECTIVITY_TEST call

---

## I2 — LogsPage prompt 展示脱敏

**根因：** `CallPromptPanel` / `PromptBlock` 原样渲染 `system_prompt` / `user_prompt` / `response_text`，executor 写入的 `recipe_id`（kebab-case）与 `operation.*` 对创作者可见。

**修复：** 新增 `sanitizePromptForDisplay`，展示前将：
- `\boperation.[a-z0-9._-]+`
- `"recipe_id": "..."` 值
- 独立 kebab-case 配方 token

替换为 `〔已隐藏〕`。下载 JSON 仍为原文。

**文件：** `frontend/src/pages/LogsPage.tsx`

**测试：** `LogsPage.test.tsx` — `redacts operation.* and recipe-like ids in expanded prompt body`

---

## I3 — System overlay PUT merge

**根因：** `save_system_overlay` 将 `_sanitize_overlay` 结果整包写入新 revision，二次 PUT 仅 `{scoring_preset}` 会丢失其余键。

**修复：**
- 后端：与上一 revision overlay merge；请求键覆盖；省略键保留；`quality_pass_threshold: null` 显式清除
- 前端：保存时以 GET 的 overlay 为基底；阈值留空且原先有覆盖 → 发 `null`；原先无覆盖 → 省略

**文件：**
- `backend/apps/drama/orchestrator/system_config.py`
- `frontend/src/pages/SystemPage.tsx`
- `frontend/src/types/v3/domain.ts`（`quality_pass_threshold?: number | null`）

**测试：**
- `test_overlay_partial_update_merges_previous`
- `test_quality_pass_threshold_null_clears_overlay`
- `test_put_partial_overlay_merges_previous`（API）
- SystemPage — `merges existing overlay and sends null when clearing threshold`

---

## Verify

```text
# Backend（31 tests）
DRAMA_SKILLS_ROOT=... py -3 manage.py test \
  apps.drama.tests.test_v3_provider_test \
  apps.drama.tests.test_v3_logs_api \
  apps.drama.tests.test_v3_system_config \
  apps.drama.tests.test_v3_system_api \
  --settings=config.settings.sqlite_test -v 1
→ OK (31 tests)

# Frontend
npm test -- src/pages/LogsPage.test.tsx src/pages/SystemPage.test.tsx
→ 13 passed (LogsPage 7 + SystemPage 6)

npm run typecheck
→ OK
```

## Report path

`.superpowers/sdd/w5-final-important-fix.md`
