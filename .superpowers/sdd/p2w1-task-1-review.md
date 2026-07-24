# P2-W1 Task 1 Review — backup_provider_ids + V3FailoverAttempt

**Reviewer:** task-scoped gate  
**Date:** 2026-07-23  
**Base:** bf922f64 · **Head:** working tree  
**Verdict:** Spec ✅ · Code quality **Approved**

---

## Spec compliance: ✅

| Requirement | Result |
|-------------|--------|
| §4.1 `V3RoleModelMapping.backup_provider_ids` — `JSONField(default=list, blank=True)` | ✅ |
| §4.2 `V3FailoverAttempt` fields (id, v3_command_run, v3_project, owner, role_key, provider, attempt_index, status, error_code, error_message, llm_call_log, created_at) | ✅ |
| Status choices: `succeeded` \| `failed_switchable` \| `failed_terminal` \| `skipped` | ✅ |
| `db_table = "drama_v3_failover_attempt"` | ✅ |
| Index `(v3_command_run, -created_at)` | ✅ |
| Migration `0020` depends on `0019`, applies only field + model | ✅ |
| Focused test via `sqlite_test` | ✅ (re-run: 1 test OK) |
| No policy/router/API/frontend in task artifacts | ✅ |

**Scope note:** Task-owned files (`0020` migration, `test_v3_failover_models.py`, and the two model blocks) are correctly scoped. The review-package diff against `bf922f64` also includes ~400 lines of unrelated V3 bootstrap and V6 models in `models.py` inherited from the working tree—not introduced by migration `0020` or the test. Does not block task deliverables but should be separated in future review packaging.

---

## Code quality: Approved

Implementation follows existing V3 conventions (UUID PK, explicit `db_table`, `TextChoices`, nullable SET_NULL FKs). Migration is minimal. Test matches the brief and proves create + default semantics.

---

## Findings

### Critical
*(none)*

### Important
1. **Review diff noise / inherited scope** — `models.py` delta from base includes V6 types (`StudioDecision`, `DramaProjectRuntime`, etc.) and full V3 model bootstrap unrelated to Task 1. Task-specific edits are limited to `backup_provider_ids` + `V3FailoverAttempt`; future gates should diff against a V3-ready base to avoid false scope flags.

### Minor
1. **Test coverage minimal by design** — only asserts default `[]` and `succeeded` create; other Status values and FK wiring (`v3_command_run`, `llm_call_log`) untested (acceptable for Task 1 brief).
2. **`provider` FK uses CASCADE** — deleting a provider removes audit rows; spec silent; SET_NULL may be preferable later but not required now.

---

## Strengths

- TDD evidence documented (RED ImportError → GREEN OK); independently verified.
- Migration `0020` contains exactly two operations—no scope creep in migration layer.
- Field names, nullability, and index match Spec §4.1/§4.2 and implementer report verbatim.
- Test provider factory aligns with brief (`api_key_encrypted` direct create).

---

## Finding counts

| Severity | Count |
|----------|-------|
| Critical | 0 |
| Important | 1 |
| Minor | 2 |
