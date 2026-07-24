# P4-W1 Report — Templates API

**Status:** DONE  
**Date:** 2026-07-23  
**Scope:** `V3ProjectTemplate` + builtin/custom templates API + create_project 挂钩

---

## Deliverables

| File | Action |
|------|--------|
| `backend/apps/drama/models.py` | Modified — `V3Project.settings`；新增 `V3ProjectTemplate` |
| `backend/apps/drama/migrations/0023_v3_project_template_and_settings.py` | Created |
| `backend/apps/drama/services/templates_service.py` | Created — builtin/custom/seed |
| `backend/apps/drama/api/v3/templates_views.py` | Created |
| `backend/apps/drama/api/v3/serializers.py` | Modified — CreateProject + custom serializers |
| `backend/apps/drama/api/v3/urls.py` | Modified — `/templates/**` |
| `backend/apps/drama/orchestrator/dispatcher.py` | Modified — `template_seed` |
| `backend/apps/drama/tests/test_v3_templates_api.py` | Created — 5 cases |
| `docs/contracts/v3/openapi.yaml` | Modified |
| `docs/superpowers/baselines/2026-07-23-p4-w1-templates-api-acceptance.md` | Created |
| `docs/superpowers/plans/2026-07-23-drama-website-v3-templates-knowledge.md` | Modified — P4-W1 ✅ |

---

## Tests

```text
py -3 manage.py test apps.drama.tests.test_v3_templates_api --settings=config.settings.sqlite_test
→ Ran 5 tests … OK
```

覆盖：list builtin+custom、staff CRUD、non-staff 403、create_project `theme_code`/`template_id` → `settings.template_seed`。

**Commit:** 跳过（按任务要求）
