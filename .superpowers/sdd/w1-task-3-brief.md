### Task 3: `/api/v3` 项目 CRUD + commands 端点

**Files:**
- Modify: `backend/apps/drama/api/v3/serializers.py`
- Modify: `backend/apps/drama/api/v3/views.py`
- Modify: `backend/apps/drama/api/v3/urls.py`
- Modify: `docs/contracts/v3/openapi.yaml`（追加 archive、commands）
- Test: `backend/apps/drama/tests/test_v3_projects_crud.py`
- Modify: 可选让 `V3ProjectListCreateView.post` 改为调用 `dispatch_command`（保持 OpenAPI 200 行为）

**Interfaces:**
- Consumes: `dispatch_command`、`V3Project`、`V3CommandRun`
- Produces HTTP:
  - `GET /api/v3/projects/?include_archived=0|1` — 默认仅 `archived_at ISNULL`
  - `POST /api/v3/projects/` — 内部 `dispatch_command(create_project)`，仍返回 `ProjectSummary`（兼容 W0）
  - `POST /api/v3/projects/{id}/archive/` — 设 `archived_at=now()`，幂等
  - `POST /api/v3/commands/` body `{command_type, payload, idempotency_key?}` → `{command_run: {...}, project?: summary}`
  - `GET /api/v3/commands/{run_id}/` — 本人运行详情

`CommandRun` 序列化字段：`id, command_type, status, project_id, error_message, result_payload, created_at, updated_at`

- [ ] **Step 1: 写 API 失败测试**

```python
# 关键用例（APITestCase + force_authenticate）
# 1) create via POST /projects/ → 200 + stage topic
# 2) list excludes archived by default
# 3) archive then list empty; include_archived=1 可见
# 4) POST /commands/ create_project → succeeded + project
# 5) POST /commands/ generate_topic_brief → unsupported
# 6) 他用户 project 404 on archive
```

完整测试文件按上列用例编写（每用例独立方法）。

- [ ] **Step 2: 运行确认至少部分失败**

```bash
py -3 manage.py test apps.drama.tests.test_v3_projects_crud -v 2 --settings=config.settings.sqlite_test
```

- [ ] **Step 3: 实现 serializers/views/urls + 更新 openapi.yaml**

`urls.py` 追加：

```python
path("projects/<uuid:project_id>/archive/", V3ProjectArchiveView.as_view()),
path("commands/", V3CommandDispatchView.as_view()),
path("commands/<uuid:run_id>/", V3CommandRunDetailView.as_view()),
```

列表 GET 读取 `include_archived` query（`"1"`/`"true"` 为真）。

- [ ] **Step 4: 全绿 + 回归 W0 冒烟**

```bash
py -3 manage.py test apps.drama.tests.test_v3_contract_smoke apps.drama.tests.test_v3_projects_crud apps.drama.tests.test_v3_orchestrator apps.drama.tests.test_v3_domain_w1 -v 2 --settings=config.settings.sqlite_test
```

Expected: 全部 PASS

---

