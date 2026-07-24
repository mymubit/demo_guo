### Task 1: 领域扩展 — 归档字段 + CommandRun

**Files:**
- Modify: `backend/apps/drama/models.py`（`V3Project`）
- Create/Modify: migration `0013_…py`（编号以 `makemigrations` 为准）
- Test: `backend/apps/drama/tests/test_v3_projects_crud.py`（本任务先写模型相关断言，或与 Task 3 合并测 API——本任务以模型+迁移可测为准）

**Interfaces:**
- Consumes: 现有 `V3Project(id, owner, title, entry_type, stage, progress_percent, created_at, updated_at)`
- Produces:
  - `V3Project.archived_at: DateTimeField(null=True, blank=True)` — `None` 表示未归档
  - `V3CommandRun` 模型字段见下方实现

- [ ] **Step 1: 写失败测试（模型字段）**

创建 `backend/apps/drama/tests/test_v3_domain_w1.py`：

```python
# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.drama.models import V3CommandRun, V3Project


class V3DomainW1Tests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username="w1u", password="pass12345")

    def test_project_can_be_archived(self) -> None:
        p = V3Project.objects.create(
            owner=self.user, title="A", entry_type="original"
        )
        self.assertIsNone(p.archived_at)
        p.archived_at = timezone.now()
        p.save(update_fields=["archived_at", "updated_at"])
        p.refresh_from_db()
        self.assertIsNotNone(p.archived_at)

    def test_command_run_defaults(self) -> None:
        run = V3CommandRun.objects.create(
            owner=self.user,
            command_type="create_project",
            status=V3CommandRun.Status.SUCCEEDED,
            request_payload={"title": "A", "entry_type": "original"},
            result_payload={},
        )
        self.assertEqual(run.command_type, "create_project")
        self.assertIsNone(run.project)
```

- [ ] **Step 2: 运行确认失败**

```bash
cd backend
py -3 manage.py test apps.drama.tests.test_v3_domain_w1 -v 2 --settings=config.settings.sqlite_test
```

Expected: FAIL（`V3CommandRun` 不存在 / `archived_at` 不存在）

- [ ] **Step 3: 实现模型**

在 `V3Project` 增加：

```python
archived_at = models.DateTimeField(null=True, blank=True, db_index=True)
```

新增：

```python
class V3CommandRun(models.Model):
    class Status(models.TextChoices):
        QUEUED = "queued", "排队"
        RUNNING = "running", "执行中"
        SUCCEEDED = "succeeded", "成功"
        FAILED = "failed", "失败"
        UNSUPPORTED = "unsupported", "本阶段未实现"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="v3_command_runs")
    project = models.ForeignKey(
        V3Project, null=True, blank=True, on_delete=models.SET_NULL, related_name="command_runs"
    )
    command_type = models.CharField(max_length=64)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.QUEUED)
    idempotency_key = models.CharField(max_length=64, blank=True, default="")
    request_payload = models.JSONField(default=dict)
    result_payload = models.JSONField(default=dict)
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_v3_command_run"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner", "-created_at"]),
            models.Index(fields=["command_type", "status"]),
        ]
```

然后：

```bash
py -3 manage.py makemigrations drama
py -3 manage.py migrate
```

注意：若 `makemigrations` 再次夹带无关 `RenameIndex`，**拆成仅含本任务字段的迁移**或在报告中标明并尽量避免。

- [ ] **Step 4: 测试通过**

同上 test 命令 → Expected: PASS

---

