# W5 Task 2 Brief

Plan Task 2: V3SystemConfigRevision + resolver

**Files:**
- Modify: `backend/apps/drama/models.py` + migration `0017_…` (check latest migration number)
- Create: `backend/apps/drama/orchestrator/system_config.py`
- Test: `test_v3_system_config.py`

**Model (verbatim):**

```python
class V3SystemConfigRevision(models.Model):
    revision = models.PositiveIntegerField(unique=True)
    overlay = models.JSONField(default=dict)
    updated_by = models.CharField(max_length=128)
    change_reason = models.CharField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "drama_v3_system_config_revision"
        ordering = ["-revision"]
```

**Resolver:**

```python
def resolve_system_config() -> dict:
    """返回 {revision, overlay, effective}；无修订时 revision=0, overlay={}. """

def save_system_overlay(*, overlay: dict, actor: str, change_reason: str = "") -> dict:
    """校验允许键 → 新 revision → 返回 resolve 结果。"""
```

Allowed overlay keys: `target_platform`, `scoring_preset`, `quality_pass_threshold`.
`effective` at least: `target_platform`, `scoring_preset`, `pass_threshold`, `platform_label_zh`.
Read foundation presets from drama-skills/foundation/presets/ (scoring-presets.yaml, platform-profiles.yaml).

Do NOT build REST yet (Task 3).
Do NOT git commit.
Work: c:\Users\99193\Desktop\demo_guo
DRAMA_SKILLS_ROOT=c:\Users\99193\Desktop\demo_guo\drama-skills
sqlite_test.

## Global Constraints
No v6_*; no new deps; skip commit.
