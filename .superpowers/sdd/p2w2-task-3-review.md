# P2-W2 Task 3 Review — Prices API GET/PUT

**Reviewer:** task-scoped gate  
**Date:** 2026-07-23  
**Scope:** `prices_views.py` + `V3ModelsService.list_prices`/`put_prices` + serializers + urls + OpenAPI + TS + `services/v3/prices.ts` + `test_v3_prices_api.py`  
**Verdict:** Spec ✅ · Code quality **Approved**

---

## Spec compliance: ✅

| Requirement | Result |
|-------------|--------|
| `GET /api/v3/models/prices/` | ✅ `V3ModelPricesView.get` → `list_prices()` |
| Response `{ items: [{ id, provider_id, provider_name, model_name, price_in_per_1k, price_out_per_1k, currency }] }` | ✅ `serialize_price` + envelope `{code,message,data}` |
| `PUT /api/v3/models/prices/` body `{ items: [...] }` | ✅ `ModelPriceTableSerializer` + `put_prices` |
| Upsert by `provider_id` + `model_name` | ✅ `update_or_create(provider, model_name, …)`；单测保留同一 `id` |
| Provider must exist | ✅ `DramaLlmProvider.objects.filter(pk=…).first()` → 400 + 无落库 |
| Prices ≥ 0 | ✅ `DecimalField(min_value=0)` on in/out |
| `IsAuthenticated` | ✅ view `permission_classes`；未登录 GET → 401/403 |
| OpenAPI paths + schemas | ✅ `/models/prices/`、`ModelPrice*`、`EnvelopeModelPriceTable` |
| Frontend types + service | ✅ `domain.ts` + `prices.ts` (`getModelPrices` / `putModelPrices`) |
| TDD 7 cases + independent re-run | ✅ `test_v3_prices_api` OK；`api.test.ts` 8 passed |

**Notes:** Brief/plan 用语「全量 upsert」与 `put_role_mappings` 一致——对 payload 内每条 `(provider_id, model_name)` 做 upsert，**不**删除 payload 外已有单价行；与 Spec §6「批量更新」语义一致，非 replace-all。`currency` 省略时默认 `CNY`（service `defaults` + serializer default）。

---

## Code quality: Approved

视图层薄、校验在 Serializer、业务在 `V3ModelsService`，与 `V3RoleModelMappingView` 模式一致。`put_prices` 使用 `@transaction.atomic`，provider 校验失败时整批回滚（单测 `missing_provider` 断言 `count=0`）。`list_prices` 使用 `select_related("provider")` 避免 N+1。OpenAPI / TS 字段与响应形状对齐。

---

## Findings

### Critical
*(none)*

### Important
*(none)*

### Minor

1. **测试缺口 — PUT 未鉴权** — 仅 `test_unauthenticated_rejected` 覆盖 GET；PUT 同样应拒绝 401/403（实现已共享 `permission_classes`，风险低）。
2. **测试缺口 — 负价仅测 `price_in`** — Serializer 对 out 同样 `min_value=0`，但未单独断言 `price_out_per_1k < 0`。
3. **测试缺口 — `model_name` 空串** — `put_prices` 有 `model_name 不能为空` 分支，无 API 测。
4. **同批重复键** — 同一 PUT 内两条相同 `(provider_id, model_name)` 时后者覆盖前者且无 400；UI 全量提交场景下概率低。
5. **默认 `currency` 未显式断言** — upsert 首包省略 `currency` 时应为 `CNY`；实现正确，测试未查首包响应/库行。

---

## Strengths

- 契约字段完整：`provider_name` 只读透出，便于 Models 页展示。
- Upsert 键与 Task 1 `UniqueConstraint(provider, model_name)` 一致。
- 7 条 TDD 覆盖空列表、创建+GET、upsert、非法 provider、负价、空 items、鉴权。
- 前端 `prices.ts` 与 `models.ts` 中 role-mappings 调用风格一致；类型经 `api.test.ts` 与 OpenAPI 交叉校验。
- 范围克制：无 Usage API / UI / rollup 改动。

---

## Verification

```powershell
cd backend
$env:DRAMA_SKILLS_ROOT="...\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_prices_api --settings=config.settings.sqlite_test -v 1
```

**Result:** OK — Ran 7 tests in ~2.6s

```powershell
cd frontend
npm test -- src/types/v3/api.test.ts --run
```

**Result:** OK — 8 tests passed

---

## Finding counts

| Severity | Count |
|----------|-------|
| Critical | 0 |
| Important | 0 |
| Minor | 5 |
