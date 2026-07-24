# P2-W2 Task 1 Report — V3ModelPrice

**Status:** DONE  
**Date:** 2026-07-23  
**Scope:** Django model + migration + focused unit tests only (no Prices API / rollup)

---

## Deliverables

| File | Action |
|------|--------|
| `backend/apps/drama/models.py` | Modified — new `V3ModelPrice` |
| `backend/apps/drama/migrations/0021_v3_model_price.py` | Created via `makemigrations` |
| `backend/apps/drama/tests/test_v3_model_price.py` | Created — TDD tests from brief |

---

## TDD Evidence

### Step 1 — RED (before implementation)

```powershell
cd c:\Users\99193\Desktop\demo_guo\backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_model_price --settings=config.settings.sqlite_test -v 1
```

**Result:** FAIL

```
ImportError: cannot import name 'V3ModelPrice' from 'apps.drama.models'
FAILED (errors=1)
```

### Step 2 — Implementation

1. **`V3ModelPrice`** — Spec §4.3 fields:
   - `provider` (FK `DramaLlmProvider`, CASCADE, `related_name="model_prices"`)
   - `model_name` (CharField 128)
   - `price_in_per_1k`, `price_out_per_1k` (DecimalField max_digits=16, decimal_places=6)
   - `currency` (CharField, default `CNY`)
   - `updated_at` (auto_now)
   - `db_table = "drama_v3_model_price"`
   - UniqueConstraint on `(provider, model_name)`

### Step 3 — GREEN (after implementation)

Same command as RED.

**Result:** OK

```
Creating test database for alias 'default'...
..
----------------------------------------------------------------------
Ran 2 tests in 0.002s

OK
```

---

## Self-Review

| Check | Result |
|-------|--------|
| Fields match Spec §4.3 | ✓ |
| Unique (provider, model_name) | ✓ |
| Migration depends on `0020` | ✓ |
| FK pattern aligned with `V3RoleModelMapping` | ✓ |
| No scope creep (Prices API / rollup) | ✓ |

**Concerns:** None blocking. Price validation (≥0) deferred to Prices PUT API (Task 3).

---

## Commit

Skipped per project rule (user did not request commit).
