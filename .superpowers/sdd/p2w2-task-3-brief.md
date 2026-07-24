### Task 3: Prices API GET/PUT

**Files:** `api/v3/prices_views.py`、`serializers`、`urls.py`、OpenAPI、TS、`services/v3/prices.ts`；Test `test_v3_prices_api.py`

**Contract:**
- `GET /api/v3/models/prices/` → `{ items: [{ id, provider_id, provider_name, model_name, price_in_per_1k, price_out_per_1k, currency }] }`
- `PUT /api/v3/models/prices/` body `{ items: [...] }` 全量 upsert（按 provider_id+model_name）；校验 provider 存在、价格 ≥0

- [ ] TDD API
- [ ] Implement
- [ ] Commit 跳过

---
