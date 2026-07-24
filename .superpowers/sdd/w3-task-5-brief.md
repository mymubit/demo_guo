### Task 5: Episodes REST API

**Files:**
- Create: `api/v3/episodes_views.py`
- Modify: `urls.py`、`serializers.py`、`openapi.yaml`
- Test: `test_v3_episodes_api.py`

**Interfaces:**

```
GET  /api/v3/projects/{id}/episodes/
  → { stage, committed, candidate, latest_run }

POST /api/v3/projects/{id}/episodes/generate/
  body: { episode_count?: int, duration_target?: str, planning_requests?: object }

POST /api/v3/projects/{id}/episodes/confirm/

POST /api/v3/projects/{id}/episodes/revise/
  body: { episode_numbers: int[], revision_requests?: object }
```

Owner 隔离；generate/revise → dispatch；confirm → `confirm_episode_plan`。

- [ ] **Step 1–4: TDD API + OpenAPI**

---

