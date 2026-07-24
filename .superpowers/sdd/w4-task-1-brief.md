# W4 Task 1 Brief

Plan: docs/superpowers/plans/2026-07-23-drama-website-v3-w4-quality-delivery.md

### Task 1: 契约说明 + `V3QualityFinding` + report meta 约定

**Files:**
- Modify: `docs/contracts/v3/commands.md`（注明 accept 同步；报告无 confirm）
- Modify: `docs/contracts/v3/openapi.yaml` — QualityState / DeliveryState / Finding
- Modify: `frontend/src/types/v3/domain.ts`、`commands.ts`（若需）
- Modify: `models.py` + migration `0016_v3_quality_finding.py`
- Create: `orchestrator/report_meta.py`
- Test: `test_v3_quality_finding.py`、`test_v3_report_meta.py`

**Interfaces — Finding:**

```python
class V3QualityFinding(models.Model):
    class Source(models.TextChoices):
        QUALITY = "quality", "质量"
        COMPLIANCE = "compliance", "合规"

    class Status(models.TextChoices):
        OPEN = "open", "待处理"
        ACCEPTED = "accepted", "已接受"
        RESOLVED = "resolved", "已解决"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(V3Project, on_delete=models.CASCADE, related_name="quality_findings")
    source = models.CharField(max_length=16, choices=Source.choices)
    finding_key = models.CharField(max_length=128)  # 稳定键：如 defect index 或 hash
    title = models.CharField(max_length=256)
    severity = models.CharField(max_length=32, blank=True, default="")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    report_artifact = models.ForeignKey(
        V3ArtifactVersion, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_v3_quality_finding"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "source", "finding_key"],
                name="uniq_v3_finding_project_source_key",
            )
        ]
```

**Interfaces — report_meta:**

```python
META_KEY = "_v3_meta"

def attach_script_meta(payload: dict, *, script_art: V3ArtifactVersion) -> dict: ...
def strip_meta_for_validate(payload: dict) -> dict: ...
def read_source_script_version(payload: dict) -> int | None: ...
def is_report_stale(*, report_payload: dict, current_script: V3ArtifactVersion | None) -> bool: ...
```

Staleness rule (from plan Global):
`is_stale = true` iff current committed `episode_scripts.version` ≠ `source_script_version` in `_v3_meta`.

Meta JSON shape:
```json
"_v3_meta": {
  "source_script_version": 3,
  "source_script_artifact_id": "<uuid>"
}
```

Steps:
- [ ] Step 1: 写失败测试（唯一约束、`is_report_stale` 真/假）
- [ ] Step 2: 实现 model + report_meta + 契约字段
- [ ] Step 3: 测试通过
- [ ] Step 4: Commit（**默认跳过** — 用户未要求 commit）

## Global Constraints (binding)

- 禁止 v6_runtime / v6_workbench / v6_control_plane
- 不引入新第三方库
- Commit 仅在用户明确要求时执行（本任务跳过 commit）
- 工作目录：c:\Users\99193\Desktop\demo_guo
- 后端：py -3 manage.py test … --settings=config.settings.sqlite_test
- DRAMA_SKILLS_ROOT 指向仓库 drama-skills
