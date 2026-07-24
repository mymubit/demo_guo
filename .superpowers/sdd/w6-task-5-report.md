# W6 Task 5 报告：删除后端 v2_* + Generation/V6 入口

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W6 — 删除后端 `v2_*` + Generation/V6 入口  
**Commits:** none（用户明确跳过）  
**Brief:** `.superpowers/sdd/w6-task-5-brief.md`  
**Plan:** `docs/superpowers/plans/2026-07-23-drama-website-v3-w6-billing-legacy-cut.md` Task 5

---

## Preconditions

- Task 3 已确认：`config/urls.py` 无 `include("apps.drama.v2_urls")`，`/api/v2/**` → `V2GoneView` 410。

---

## What I Deleted / Changed

### Deleted modules

| 路径 | 说明 |
|------|------|
| `v2_urls.py` / `v2_views.py` / `v2_serializers.py` / `v2_service.py` | 旧 Studio HTTP + 服务层 |
| `services/v6_runtime.py` / `v6_workbench.py` / `v6_control_plane.py` | 旧 V6 编排入口 |
| `services/generation_service.py` | 旧 job 主链（依赖 V6Runtime） |

### Deleted tests（仅旧链）

- `tests/test_v2_studio_api.py`
- `tests/test_v6_runtime.py`
- `tests/test_generation.py`
- `tests/test_substance_gates_wiring.py`

### Rewritten / minor

- `tasks.py` → 空壳模块（docstring only），Celery `autodiscover_tasks()` 仍可加载；无 `GenerationService`、无假 `ImportError` stub
- `services/artifact_ingest.py` → 注释去掉 `GenerationService` 字样（满足 grep 清零）

### 明确保留

- `tasks_v3.py`、`api/v3/**`、`orchestrator/**`、`skills_bridge/**`
- `services/generation_gate.py`（无 V3 import；纯门禁，不在删除清单）

---

## Grep（完成条件）

```bash
rg -n "GenerationService|from apps\.drama\.v2|apps\.drama\.services\.v6_runtime|apps\.drama\.services\.v6_workbench|apps\.drama\.services\.v6_control_plane" backend/apps/drama -g "!migrations/**" -g "!**/__pycache__/**"
```

**结果：** ZERO matches（exit 1 / RG_ZERO）

无 `try/except ImportError` 假存活。

---

## Verification

```bash
cd backend
py -3 manage.py check --settings=config.settings.sqlite_test
py -3 manage.py test apps.drama.tests.test_v3_contract_smoke apps.drama.tests.test_v2_gone --settings=config.settings.sqlite_test -v 1
```

| 命令 | 结果 |
|------|------|
| `manage.py check` | 0 issues |
| `test_v3_contract_smoke` + `test_v2_gone` | 6 passed，exit 0 |

---

## Files Changed

| 路径 | 操作 |
|------|------|
| `backend/apps/drama/v2_*.py`（4） | 删除 |
| `backend/apps/drama/services/v6_{runtime,workbench,control_plane}.py` | 删除 |
| `backend/apps/drama/services/generation_service.py` | 删除 |
| `backend/apps/drama/tests/test_{v2_studio_api,v6_runtime,generation,substance_gates_wiring}.py` | 删除 |
| `backend/apps/drama/tasks.py` | 改写为空壳 |
| `backend/apps/drama/services/artifact_ingest.py` | 注释微调 |
| `.superpowers/sdd/w6-task-5-report.md` | 本报告 |

---

## Concerns

1. `backend/README.md` 仍描述 `v2_*` / `v6_*`（文档滞后，非本 Task 范围）。
2. `generation_gate.py` / `skills_loader.v6_workbench` 属性名仍在；不在 banned import 列表，留给后续若需再收。
3. 旧 Celery 任务名（`run_generation_task` 等）已无注册；队列中若有历史消息会找不到 task（预期，产品已切 `tasks_v3`）。

---

## Reviewer Verdict

**Spec:** ✅  
**Quality:** Approved

**Independent checks (2026-07-23):**
- `v2_*.py`、`v6_{runtime,workbench,control_plane}.py`、`generation_service.py` 及 4 个旧测文件：磁盘已不存在（12/12 `Test-Path` False）
- `config/urls.py`：无 `v2_urls` include，`/api/v2/**` → `V2GoneView` 410
- `tasks.py`：空壳可 import；无 `ImportError` stub
- Banned `rg`：`RG_ZERO`（exit 1）
- `manage.py check`：0 issues
- `test_v3_contract_smoke` + `test_v2_gone`：6 passed

**Findings:** None.

**Residual (non-blocking):** `skills_loader.v6_workbench` 属性名、`generation_gate.get_v6_workbench_operation` 仍在；不在 banned import 列表，与报告 Concerns #2 一致。
