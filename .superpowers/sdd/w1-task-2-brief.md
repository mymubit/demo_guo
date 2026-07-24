### Task 2: 编排器骨架（同步 create_project + 异步桩）

**Files:**
- Create: `backend/apps/drama/orchestrator/types.py`
- Create: `backend/apps/drama/orchestrator/dispatcher.py`
- Create: `backend/apps/drama/orchestrator/__init__.py`
- Test: `backend/apps/drama/tests/test_v3_orchestrator.py`

**Interfaces:**
- Consumes: `V3Project`, `V3CommandRun`, `PRODUCT` command types from `docs/contracts/v3/commands.md`
- Produces:
  - `dispatch_command(*, owner, command_type: str, payload: dict, idempotency_key: str = "") -> V3CommandRun`
  - 同步：`create_project` → 创建项目，`status=succeeded`，`result_payload={"project_id": "..."}`，`project` FK 已设
  - 异步白名单（W2+）：`generate_topic_brief` 等 → `status=unsupported`，`error_message` 含人话「将在后续里程碑开放」，**不** import skills / LLM
  - 未知 `command_type` → `status=failed`，`error_message` 说明非法命令

- [ ] **Step 1: 写失败测试**

```python
# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.drama.models import V3CommandRun, V3Project
from apps.drama.orchestrator import dispatch_command


class V3OrchestratorTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username="orch", password="pass12345")

    def test_create_project_succeeds_sync(self) -> None:
        run = dispatch_command(
            owner=self.user,
            command_type="create_project",
            payload={"title": "新剧", "entry_type": "adapt"},
        )
        self.assertEqual(run.status, V3CommandRun.Status.SUCCEEDED)
        self.assertIsNotNone(run.project_id)
        project = V3Project.objects.get(id=run.project_id)
        self.assertEqual(project.title, "新剧")
        self.assertEqual(project.entry_type, "adapt")
        self.assertEqual(project.stage, "topic")
        self.assertEqual(str(run.result_payload.get("project_id")), str(project.id))

    def test_async_command_is_unsupported_stub(self) -> None:
        project = V3Project.objects.create(owner=self.user, title="P", entry_type="original")
        run = dispatch_command(
            owner=self.user,
            command_type="generate_topic_brief",
            payload={"project_id": str(project.id)},
        )
        self.assertEqual(run.status, V3CommandRun.Status.UNSUPPORTED)
        self.assertIn("后续", run.error_message)

    def test_unknown_command_fails(self) -> None:
        run = dispatch_command(
            owner=self.user,
            command_type="create-project-brief",
            payload={},
        )
        self.assertEqual(run.status, V3CommandRun.Status.FAILED)
```

- [ ] **Step 2: 运行确认失败**

```bash
py -3 manage.py test apps.drama.tests.test_v3_orchestrator -v 2 --settings=config.settings.sqlite_test
```

Expected: FAIL（模块不存在）

- [ ] **Step 3: 实现 dispatcher**

`types.py`：定义 `SYNC_COMMANDS = frozenset({"create_project"})` 与 `ASYNC_STUB_COMMANDS`（commands.md 中除 `create_project` 外全部）。

`dispatcher.py` 核心逻辑（示意）：

```python
def dispatch_command(*, owner, command_type: str, payload: dict, idempotency_key: str = "") -> V3CommandRun:
    run = V3CommandRun.objects.create(
        owner=owner,
        command_type=command_type,
        status=V3CommandRun.Status.RUNNING,
        idempotency_key=idempotency_key or "",
        request_payload=payload or {},
    )
    if command_type == "create_project":
        title = (payload or {}).get("title") or ""
        entry_type = (payload or {}).get("entry_type") or ""
        if not title or entry_type not in ("original", "adapt"):
            run.status = V3CommandRun.Status.FAILED
            run.error_message = "标题与创作来源（原创/改编）不能为空"
            run.save(update_fields=["status", "error_message", "updated_at"])
            return run
        project = V3Project.objects.create(
            owner=owner, title=title[:200], entry_type=entry_type, stage=V3Project.Stage.TOPIC
        )
        run.project = project
        run.status = V3CommandRun.Status.SUCCEEDED
        run.result_payload = {"project_id": str(project.id)}
        run.save(update_fields=["project", "status", "result_payload", "updated_at"])
        return run
    if command_type in ASYNC_STUB_COMMANDS:
        run.status = V3CommandRun.Status.UNSUPPORTED
        run.error_message = "该创作命令将在后续里程碑开放，当前仅完成项目与仪表盘"
        run.save(update_fields=["status", "error_message", "updated_at"])
        return run
    run.status = V3CommandRun.Status.FAILED
    run.error_message = "未知命令"
    run.save(update_fields=["status", "error_message", "updated_at"])
    return run
```

`__init__.py`：`from .dispatcher import dispatch_command`

- [ ] **Step 4: 测试通过**

同上 → PASS

---

