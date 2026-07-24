### Task 1: `V3ArtifactVersion` + 可选 Draft

**Files:**
- Modify: `backend/apps/drama/models.py`
- Create: migration `0014_…`
- Test: `backend/apps/drama/tests/test_v3_artifact.py`

**Interfaces:**
- Produces model:

```python
class V3ArtifactVersion(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "草稿"
        CANDIDATE = "candidate", "候选"
        COMMITTED = "committed", "已确认"
        SUPERSEDED = "superseded", "已替代"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(V3Project, on_delete=models.CASCADE, related_name="artifacts")
    artifact_key = models.CharField(max_length=64)  # project_brief, story_bible, ...
    version = models.PositiveIntegerField()
    schema_version = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=16, choices=Status.choices)
    payload = models.JSONField(default=dict)
    command_run = models.ForeignKey(
        V3CommandRun, null=True, blank=True, on_delete=models.SET_NULL, related_name="artifacts"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "drama_v3_artifact_version"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "artifact_key", "version"],
                name="uniq_v3_artifact_version",
            ),
        ]
```

Helper（可放 `orchestrator/artifacts.py` 或 model 方法）：

```python
def next_version(project_id, artifact_key) -> int: ...
def latest(project, artifact_key, status=None) -> V3ArtifactVersion | None: ...
```

- [ ] **Step 1: 写失败测试** — 创建 candidate、unique (project,key,version)

- [ ] **Step 2: 跑测 FAIL**

```bash
py -3 manage.py test apps.drama.tests.test_v3_artifact -v 2 --settings=config.settings.sqlite_test
```

- [ ] **Step 3: 模型 + migrate**

- [ ] **Step 4: 测 PASS**

---

