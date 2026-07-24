# P2-W2 Task 3 Report — Prices API GET/PUT

**Status:** DONE  
**Date:** 2026-07-23

## Deliverables

| File | Action |
|------|--------|
| `backend/apps/drama/tests/test_v3_prices_api.py` | Created — 7 TDD cases |
| `backend/apps/drama/api/v3/prices_views.py` | Created — `V3ModelPricesView` |
| `backend/apps/drama/api/v3/models_service.py` | Modified — `list_prices` / `put_prices` |
| `backend/apps/drama/api/v3/serializers.py` | Modified — price table serializers |
| `backend/apps/drama/api/v3/urls.py` | Modified — `models/prices/` |
| `docs/contracts/v3/openapi.yaml` | Modified — paths + schemas |
| `frontend/src/types/v3/domain.ts` | Modified — `ModelPrice*` types |
| `frontend/src/types/v3/api.ts` | Modified — exports |
| `frontend/src/types/v3/api.test.ts` | Modified — contract checks |
| `frontend/src/services/v3/prices.ts` | Created — `getModelPrices` / `putModelPrices` |

## TDD Evidence

**RED:** 7 failures — `404 Not Found` on `/api/v3/models/prices/`

**GREEN:**
```powershell
cd c:\Users\99193\Desktop\demo_guo\backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_prices_api --settings=config.settings.sqlite_test -v 1
# Ran 7 tests — OK
```

Frontend: `npm test -- src/types/v3/api.test.ts --run` — 8 passed

## Contract

- **GET** `/api/v3/models/prices/` → `{ items: [{ id, provider_id, provider_name, model_name, price_in_per_1k, price_out_per_1k, currency }] }`
- **PUT** body `{ items: [...] }` — upsert by `provider_id`+`model_name`; provider must exist; prices ≥ 0; `IsAuthenticated`

## Commit

Skipped per instruction.
