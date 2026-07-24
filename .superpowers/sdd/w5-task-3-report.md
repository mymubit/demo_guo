# W5 Task 3 报告：System REST + 配置注入质检路径

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W5 — `GET/PUT /api/v3/system/config/` + score/compliance prompt 注入  
**Commits:** none（用户明确要求不 commit）  
**Brief:** `.superpowers/sdd/w5-task-3-brief.md`

---

## What I Implemented

### 1. REST `api/v3/system_views.py`

| Method | Path | 行为 |
|--------|------|------|
| GET | `/api/v3/system/config/` | `resolve_system_config()` → `{revision, overlay, effective}` |
| PUT | `/api/v3/system/config/` | body `{overlay, change_reason?}` → `save_system_overlay` |

- 信封 `{code, message, data}`；`IsAuthenticated`
- 校验走 Task 2：未知键 warn+忽略；非法 enum / threshold → `BusinessException` 400
- 全局配置（无 owner FK）；`updated_by` = 当前用户 `username`

### 2. Serializer + urls

- `SystemConfigPutSerializer`：`overlay`（dict）+ 可选 `change_reason`
- `urls.py`：`path("system/config/", V3SystemConfigView)`

### 3. Prompt 注入（`skills_bridge/executor.py`）

对 `score_quality` / `check_compliance`，`_build_prompt` 读取 `resolve_system_config()["effective"]`，写入 user JSON：

- 顶层：`scoring_preset`、`target_platform`（便于断言）
- 嵌套：`system_config`（含 `pass_threshold`、`platform_label_zh`）

### 4. 测试

- 新建 `test_v3_system_api.py`（5）：默认 GET、PUT+GET 一致、非法 preset、未知键忽略、未登录拒
- 扩展 `test_v3_quality_executor.py`：`test_score_and_compliance_prompt_inject_system_config`

---

## TDD: RED → GREEN

### RED

```bash
cd backend
$env:DRAMA_SKILLS_ROOT='c:\Users\99193\Desktop\demo_guo\drama-skills'
py -3 manage.py test apps.drama.tests.test_v3_system_api `
  apps.drama.tests.test_v3_quality_executor.QualityExecutorDirectCommitTests.test_score_and_compliance_prompt_inject_system_config `
  -v 1 --settings=config.settings.sqlite_test
```

失败：`404`（路由未挂）+ prompt 无 `scoring_preset`/`target_platform`。

### GREEN

同 settings 复跑：

- `test_v3_system_api` + `test_v3_quality_executor` + `test_v3_system_config` → **21/21 OK**

---

## Self-Review

- [x] GET/PUT System REST + 信封 + Auth
- [x] 复用 Task 2 `resolve_system_config` / `save_system_overlay`
- [x] score/compliance prompt 可断言注入
- [x] 无 v6_* / 无新依赖 / mock LLM
- [x] 未 commit

### Concerns（非阻塞）

1. **OpenAPI `additionalProperties: false`**：契约拒未知键；实现层仍 warn+忽略（与 Task 2 / W5 Global 一致）。前端若严格按 schema 发请求无冲突。
2. **`prepare_delivery` 未注入**：计划「生效」含交付；本 Task brief 仅要求 score/compliance。后续可对称扩展。
3. **顶层 + `system_config` 双写**：为测断言与可读性；LLM 上下文略冗余，可接受。

### 风险

低。REST 薄封装；注入仅两条 command。

---

## Files Touched

| 路径 | 操作 |
|------|------|
| `backend/apps/drama/api/v3/system_views.py` | 新建 |
| `backend/apps/drama/api/v3/urls.py` | +system/config |
| `backend/apps/drama/api/v3/serializers.py` | +`SystemConfigPutSerializer` |
| `backend/apps/drama/skills_bridge/executor.py` | score/compliance 注入 |
| `backend/apps/drama/tests/test_v3_system_api.py` | 新建 |
| `backend/apps/drama/tests/test_v3_quality_executor.py` | +注入断言 |
| `.superpowers/sdd/w5-task-3-report.md` | 本报告 |

---

## Follow-ups

- Task 4：Models 映射 REST（migration **0018**）
- 可选：`prepare_delivery` 同样注入 `target_platform`

---

## Reviewer Checklist

| 必检项 | 结果 |
|--------|------|
| GET/PUT `/api/v3/system/config/` | ✅ |
| 信封 + Auth | ✅ |
| Overlay 校验对齐 Task 2 | ✅ |
| score/compliance prompt 含 preset/platform | ✅ |
| 测试 | ✅ 21/21（本任务相关套件） |
| commit | ✅ 无 |

---

## Reviewer Verdict

**Spec:** ✅ **Quality:** Approved

Brief 五项必检均满足：`GET/PUT /api/v3/system/config/`（`system_views.py` + `urls.py`）、`{code,message,data}` 信封、`IsAuthenticated`、复用 Task 2 `resolve_system_config`/`save_system_overlay`（未知键 warn+忽略、非法 enum 400）；`executor.py` 对 `score_quality`/`check_compliance` 注入 `scoring_preset`/`target_platform`/`system_config`；`test_v3_system_api.py`（5）+ `test_score_and_compliance_prompt_inject_system_config` 可断言。

本地复跑相关套件 **15/15 OK**（`sqlite_test` + `DRAMA_SKILLS_ROOT`）。无 v6_*、无 commit。

**非阻塞：** REST 未单测非法 `target_platform`（Task 2 已覆盖）；`prepare_delivery` 未注入（brief 未要求）。报告「21/21」为更宽套件计数，本任务子集 15 即可。
