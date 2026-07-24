### Task 5: Topic / Blueprint REST API

**Files:**
- Create: `backend/apps/drama/api/v3/topic_views.py`、`blueprint_views.py`（或合并 `artifacts_views.py`）
- Modify: `serializers.py`、`urls.py`
- Modify: `docs/contracts/v3/openapi.yaml`
- Test: `test_v3_topic_api.py`、`test_v3_blueprint_api.py`

**Interfaces（均需登录 + owner）：**

```
GET  /api/v3/projects/{id}/topic/
  → { stage, committed: ProjectBrief|null, candidate: ProjectBrief|null, draft: ...|null, latest_run: CommandRunSummary|null }

PUT  /api/v3/projects/{id}/topic/draft/
  body: { payload: object } → draft artifact

POST /api/v3/projects/{id}/topic/generate/
  → 等价 dispatch generate_topic_brief（可内部调 dispatch_command）

POST /api/v3/projects/{id}/topic/confirm/
  body: { use_draft?: bool } → confirm_topic_brief

GET  /api/v3/projects/{id}/blueprint/
  → { committed: {story_bible, ...}|null, candidate: {...}|null, latest_run }

POST /api/v3/projects/{id}/blueprint/generate/
POST /api/v3/projects/{id}/blueprint/confirm/
```

响应字段用业务名；可附 `artifact_key` 给前端映射，但 UI 文案仍用中文。

- [ ] **Step 1: API 测试（eager + mock）覆盖 generate→get 见 candidate→confirm→get 见 committed**

- [ ] **Step 2–4: 实现 + OpenAPI 更新 + PASS**；回归 W1 CRUD 测试

---

