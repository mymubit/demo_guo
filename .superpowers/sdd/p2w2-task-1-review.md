# P2-W2 Task 1 Review — V3ModelPrice

**Reviewer:** task-scoped gate  
**Date:** 2026-07-23  
**Scope:** `V3ModelPrice` model + migration `0021` + `test_v3_model_price.py` only  
**Verdict:** Spec ✅ · Code quality **Approved**

---

## Spec compliance: ✅

| Requirement | Result |
|-------------|--------|
| `provider` FK → `DramaLlmProvider` | ✅ CASCADE, `related_name="model_prices"` |
| `model_name` (CharField, aligns with call log) | ✅ `max_length=128` |
| `price_in_per_1k` / `price_out_per_1k` (Decimal) | ✅ `max_digits=16`, `decimal_places=6` |
| `currency` default `CNY` | ✅ model + migration default |
| unique `(provider, model_name)` | ✅ `UniqueConstraint` (`uniq_v3_model_price_provider_model`) |
| `db_table = "drama_v3_model_price"` | ✅ model Meta + migration options |
| Migration `0021` depends on `0020` | ✅ |
| Focused test via `sqlite_test` | ✅ (re-run: 2 tests OK) |
| No Prices API / rollup / frontend in task artifacts | ✅ |

**Notes:** Brief wording uses `unique_together`; implementation uses `UniqueConstraint` — equivalent and preferred in Django 4+. Spec §4.3 table omits `updated_at`; field is present and matches sibling V3 models (`V3RoleModelMapping`).

---

## Code quality: Approved

Implementation is minimal, scoped, and aligned with existing V3 FK/`db_table` conventions. Migration is a single `CreateModel` with correct constraints. Tests cover brief TDD cases (create + default currency, duplicate integrity error). TDD RED→GREEN evidence in report is credible; independently verified.

---

## Findings

### Critical
*(none)*

### Important
*(none)*

### Minor
1. **Test coverage minimal by design** — only default currency + unique conflict; no cross-provider same `model_name`, decimal precision edge, or `__str__` (acceptable for Task 1 brief).
2. **`provider` FK uses CASCADE** — deleting a provider removes price rows; spec silent; consistent with `V3RoleModelMapping`; SET_NULL may be preferable later if prices should survive provider cleanup.
3. **Non-negative price validation deferred** — no DB/model check for `price_* >= 0`; report correctly defers to Prices PUT API (Task 3).

---

## Strengths

- Spec §4.3 fields and uniqueness match verbatim; no scope creep.
- Migration `0021` is isolated (one operation, correct dependency chain).
- FK pattern mirrors `V3RoleModelMapping` (`DramaLlmProvider`, CASCADE, explicit `db_table`).
- TDD workflow documented; tests pass on `config.settings.sqlite_test`.

---

## Finding counts

| Severity | Count |
|----------|-------|
| Critical | 0 |
| Important | 0 |
| Minor | 3 |
