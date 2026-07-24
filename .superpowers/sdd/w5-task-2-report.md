# W5 Task 2 报告：V3SystemConfigRevision + resolver

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W5 — `V3SystemConfigRevision` + `resolve_system_config` / `save_system_overlay`  
**Commits:** none（用户明确要求不 commit）  
**Brief:** `.superpowers/sdd/w5-task-2-brief.md`

---

## What I Implemented

### 1. Model `V3SystemConfigRevision`（`models.py`）

按 brief 字面字段：`revision`（unique）、`overlay`、`updated_by`、`change_reason`、`created_at`；`db_table=drama_v3_system_config_revision`；`ordering=["-revision"]`。

### 2. Migration `0017_v3_system_config_revision.py`

- 最新已有 `0016_v3_quality_finding`（W4），故本任务为 **0017**（依赖 0016）。
- `makemigrations` 生成；含隐式 `BigAutoField` PK（与 Django 默认一致；业务键仍是 `revision`）。

### 3. Resolver `orchestrator/system_config.py`

| 函数 | 行为 |
|------|------|
| `resolve_system_config()` | `{revision, overlay, effective}`；无修订 → `revision=0, overlay={}` |
| `save_system_overlay(...)` | 允许键校验 → `revision+1`（`select_for_update`）→ 返回 resolve 结果 |

- 允许 overlay 键：`target_platform` / `scoring_preset` / `quality_pass_threshold`
- 未知键：**忽略并 `logger.warning`**（对齐 W5 Global「其余忽略并记 warn」）
- `effective`：`target_platform`, `scoring_preset`, `pass_threshold`, `platform_label_zh`
- Foundation：`foundation/presets/scoring-presets.yaml` + `platform-profiles.yaml`（经 `SkillsBundleLoader.load_seed_yaml`）
- 未指定 `scoring_preset` 时走 `platform_recommendations`；`quality_pass_threshold` 覆盖预设 `pass_threshold`
- Overlay **整单替换**（非与上一 revision 合并）

### 4. 测试 `test_v3_system_config.py`

9 cases：默认 resolve、revision 递增、平台推荐、阈值覆盖、未知键忽略、非法 preset/platform/threshold、替换语义。

---

## TDD: RED → GREEN

### Step 1: RED

```bash
cd backend
$env:DRAMA_SKILLS_ROOT='c:\Users\99193\Desktop\demo_guo\drama-skills'
py -3 manage.py test apps.drama.tests.test_v3_system_config -v 1 --settings=config.settings.sqlite_test
```

失败：`ImportError: cannot import name 'V3SystemConfigRevision'`。

### Step 2–3: 实现 + GREEN

同命令复跑 → **9 tests OK**。

---

## Self-Review

- [x] Model + migration 0017（接 0016）
- [x] resolver 无 REST（Task 3）
- [x] 未引入 v6_* / 新依赖
- [x] 未 commit
- [x] sqlite_test + DRAMA_SKILLS_ROOT 指向仓库 drama-skills

### Concerns（非阻塞）

1. **Overlay 替换语义**：PUT/save 整单替换；若产品期望「与上一 revision 合并」，Task 3 REST 落地前需确认。
2. **OpenAPI `additionalProperties: false`**：实现层忽略未知键；REST 层（Task 3）若严格拒未知键需与契约对齐。
3. **本地 env**：机器若残留 `DRAMA_SKILLS_ROOT=\app\drama-skills` 会导致 helpers fixture 读失败；测跑需显式指向仓库路径。

### 风险

低。无 REST/生成路径注入；仅模型与纯函数 resolver。

---

## Files Touched

| 路径 | 操作 |
|------|------|
| `backend/apps/drama/models.py` | +`V3SystemConfigRevision` |
| `backend/apps/drama/migrations/0017_v3_system_config_revision.py` | 新建 |
| `backend/apps/drama/orchestrator/system_config.py` | 新建 |
| `backend/apps/drama/tests/test_v3_system_config.py` | 新建 |
| `.superpowers/sdd/w5-task-2-report.md` | 本报告 |

---

## Follow-ups

- Task 3：System REST + 质检路径读 `resolve_system_config()["effective"]`
- Task 4：Models 映射若需独立迁移 → **0018**

---

## Reviewer Verdict

**Spec:** ✅  
**Quality:** Ready for review

| 必检项 | 结果 |
|--------|------|
| Model 字段/表名/ordering | ✅ 与 brief 一致 |
| Migration 编号 | ✅ 0017（依赖 0016） |
| resolve / save API | ✅ |
| effective 四字段 + presets | ✅ |
| 未知键 warn、允许键校验 | ✅ |
| REST | ✅ 未做 |
| 测试 | ✅ 9/9 |
| commit | ✅ 无 |

---

## Reviewer Verdict

**Spec:** ✅  
**Quality:** Approved

| 必检项 | 结果 |
|--------|------|
| `V3SystemConfigRevision` 字段/表名/ordering | ✅ 与 brief 字面一致 |
| Migration `0017`（依赖 `0016`） | ✅ |
| `resolve_system_config` / `save_system_overlay` | ✅ 签名与语义正确；`select_for_update` 递增 revision |
| `effective` 四字段 + foundation presets | ✅ 经 `load_seed_yaml` 读 scoring/platform YAML |
| 允许键校验 / 未知键 warn | ✅ |
| 无 REST / 无 v6_* / 无新依赖 | ✅ |
| 测试 | ✅ 9/9 通过（独立复跑确认） |

**备注（非阻塞）：** overlay 整单替换已测但未在 brief 明示，Task 3 REST 需与产品确认；`overlay` 非 dict / bool threshold 有校验无单测；`updated_by` 空串未拒。
