# P2-W1 Task 1 Report — backup_provider_ids + V3FailoverAttempt

**Status:** DONE  
**Date:** 2026-07-23  
**Scope:** Django models + migration + focused unit test only (no policy/router/API/frontend)

---

## Deliverables

| File | Action |
|------|--------|
| `backend/apps/drama/models.py` | Modified — `V3RoleModelMapping.backup_provider_ids`; new `V3FailoverAttempt` |
| `backend/apps/drama/migrations/0020_v3_failover_attempt_and_backup_ids.py` | Created via `makemigrations` |
| `backend/apps/drama/tests/test_v3_failover_models.py` | Created — TDD test from brief |

---

## TDD Evidence

### Step 1 — RED (before implementation)

```powershell
cd c:\Users\99193\Desktop\demo_guo\backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_failover_models --settings=config.settings.sqlite_test -v 1
```

**Result:** FAIL

```
ImportError: cannot import name 'V3FailoverAttempt' from 'apps.drama.models'
FAILED (errors=1)
```

### Step 2 — Implementation

1. **`V3RoleModelMapping.backup_provider_ids`** — `JSONField(default=list, blank=True)` per Spec §4.1.
2. **`V3FailoverAttempt`** — Spec §4.2 fields:
   - `id` (UUID PK)
   - `v3_command_run` (FK, nullable, SET_NULL)
   - `v3_project` (FK, nullable, SET_NULL)
   - `owner` (FK User, CASCADE)
   - `role_key`, `provider` (FK), `attempt_index`
   - `status` TextChoices: `succeeded` | `failed_switchable` | `failed_terminal` | `skipped`
   - `error_code`, `error_message`, `llm_call_log` (FK null), `created_at`
   - `db_table = "drama_v3_failover_attempt"`
   - Index: `(v3_command_run, -created_at)`

### Step 3 — GREEN (after implementation)

Same command as RED.

**Result:** OK

```
Creating test database for alias 'default'...
.
----------------------------------------------------------------------
Ran 1 test in 0.370s

OK
```

---

## Self-Review

| Check | Result |
|-------|--------|
| Fields match Spec §4.1 / §4.2 | ✓ |
| Status enum values match brief | ✓ |
| Index on `v3_command_run, -created_at` | ✓ |
| Migration depends on `0019` | ✓ |
| No scope creep (policy/router/API) | ✓ |
| Provider create pattern aligned with brief (direct `api_key_encrypted`) | ✓ |
| Follows existing V3 model conventions (UUID PK, `db_table`, TextChoices) | ✓ |

**Concerns:** None blocking. Backup ID validation (no duplicate primary, enabled check) deferred to write API per Spec §4.1 — out of scope for Task 1.

---

## Commit

Skipped per project rule (user did not request commit).
