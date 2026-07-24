# P4-W2 Report — Knowledge API

**Status:** DONE  
**Date:** 2026-07-23  
**Scope:** 只读知识库 list / search / get-by-path（防穿越）

## Deliverables

| File | Action |
|------|--------|
| `backend/apps/drama/orchestrator/knowledge_catalog.py` | Created — `list_docs` / `read_doc` |
| `backend/apps/drama/api/v3/knowledge_views.py` | Created |
| `backend/apps/drama/api/v3/urls.py` | Modified — `/knowledge/**` |
| `backend/apps/drama/tests/test_v3_knowledge_api.py` | Created — 7 cases |
| `docs/contracts/v3/openapi.yaml` | Modified |
| `docs/superpowers/baselines/2026-07-23-p4-w2-knowledge-api-acceptance.md` | Created |
| `docs/superpowers/plans/2026-07-23-drama-website-v3-templates-knowledge.md` | Modified — P4-W2 ✅ |

## Tests

```text
DRAMA_SKILLS_ROOT=…/drama-skills
py -3 manage.py test apps.drama.tests.test_v3_knowledge_api --settings=config.settings.sqlite_test
→ Ran 7 tests … OK
```

覆盖：列表+section、q 搜索、doc 读取、穿越 400、缺失 404、未登录 401。

**Commit:** 跳过（按任务要求）
