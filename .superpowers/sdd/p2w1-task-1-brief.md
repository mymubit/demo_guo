### Task 1: 数据模型 — backup_provider_ids + V3FailoverAttempt

**Files:**
- Modify: `backend/apps/drama/models.py`
- Create: `backend/apps/drama/migrations/0020_v3_failover_attempt_and_backup_ids.py`
- Test: `backend/apps/drama/tests/test_v3_failover_models.py`

**Interfaces:**
- Produces: `V3RoleModelMapping.backup_provider_ids: list`（JSONField default `list`）
- Produces: model `V3FailoverAttempt` with fields per Spec §4.2；`Status` TextChoices: `succeeded` | `failed_switchable` | `failed_terminal` | `skipped`
- Consumes: existing `DramaLlmProvider`, `V3CommandRun`, `V3Project`, `DramaLlmCallLog`, `AUTH_USER_MODEL`

- [ ] **Step 1: Write the failing test**

```python
# test_v3_failover_models.py
from django.contrib.auth import get_user_model
from django.test import TestCase
from apps.drama.models import (
    DramaLlmProvider,
    V3FailoverAttempt,
    V3Project,
    V3RoleModelMapping,
)

class FailoverModelTests(TestCase):
    def test_mapping_backup_ids_default_empty_and_attempt_create(self):
        user = get_user_model().objects.create_user("m1", password="x")
        p1 = DramaLlmProvider.objects.create(
            name="A", base_url="https://a.example", model_name="m",
            api_key_encrypted="x", is_enabled=True,
        )
        mapping = V3RoleModelMapping.objects.create(
            role_key="drama-script-writer", provider=p1
        )
        self.assertEqual(mapping.backup_provider_ids, [])
        project = V3Project.objects.create(
            owner=user, title="t", entry_type="original", stage="topic"
        )
        attempt = V3FailoverAttempt.objects.create(
            owner=user,
            v3_project=project,
            role_key="drama-script-writer",
            provider=p1,
            attempt_index=0,
            status=V3FailoverAttempt.Status.SUCCEEDED,
        )
        self.assertEqual(attempt.status, "succeeded")
```

（若 `DramaLlmProvider` 构造字段与仓库不一致，按现有 `test_v3_models_api` 的 create 方式对齐。）

- [ ] **Step 2: Run test to verify it fails**

```powershell
cd c:\Users\99193\Desktop\demo_guo\backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_failover_models --settings=config.settings.sqlite_test -v 1
```

Expected: FAIL（模型/字段不存在）

- [ ] **Step 3: Write minimal implementation**

在 `models.py`：

1. `V3RoleModelMapping` 增加：
```python
backup_provider_ids = models.JSONField(default=list, blank=True)
```

2. 新增 `V3FailoverAttempt`（`db_table = "drama_v3_failover_attempt"`），字段对齐 Spec §4.2；索引：`v3_command_run`, `-created_at`。

3. `makemigrations` → `0020_…`（名称可微调，但必须可 apply）。

- [ ] **Step 4: Run test to verify it passes**

同 Step 2；Expected: OK

- [ ] **Step 5: Commit** — 跳过（除非用户要求）

---
