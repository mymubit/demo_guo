### Task 6: Scripts REST API + 草稿

**Files:**
- Create: `api/v3/scripts_views.py`
- Test: `test_v3_scripts_api.py`

**Interfaces:**

```
GET  /api/v3/projects/{id}/scripts/
  → { committed, candidate, drafts: [{episode_number, payload, updated_at}], latest_run }

GET  /api/v3/projects/{id}/scripts/{episode_number}/
  → 单集视图：committed 切片 + draft + candidate 切片

PUT  /api/v3/projects/{id}/scripts/{episode_number}/draft/
  body: { payload }

POST /api/v3/projects/{id}/scripts/generate/
  body: { start: int, end: int, writing_requests?: object }

POST /api/v3/projects/{id}/scripts/confirm/
  body: { use_drafts?: bool }
  # use_drafts=true：将各集 draft 合并进 scripts 结构后作为新 committed（须 validate）；否则确认 AI candidate
```

- [ ] **Step 1–4: TDD**；`use_drafts` 路径必须跑 `validate_artifact_payload("episode_scripts", ...)`（消化 W2 draft 未校验债）

---

