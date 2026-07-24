# Models 内联定价 Implementation Plan

> **For agentic workers:** 按任务逐步执行；每任务以测试门禁结束。未要求不 commit。

**Goal:** 供应商卡片内联编辑输入/输出单价；双空删除单价行；Usage 可估费。

**Architecture:** 复用 `V3ModelPrice` + PUT upsert；新增 DELETE by id；ModelsPage 并行拉 prices，按 provider 回填/保存。

**Tech Stack:** Django/DRF、既有 `V3ModelsService`、React Query、vitest。

**Spec:** `docs/superpowers/specs/2026-07-24-models-inline-prices-design.md`

## File map

| 文件 | 职责 |
|------|------|
| `backend/apps/drama/api/v3/models_service.py` | `delete_price(id)` |
| `backend/apps/drama/api/v3/prices_views.py` + `urls.py` | DELETE 路由 |
| `docs/contracts/v3/openapi.yaml` | 契约 |
| `backend/apps/drama/tests/test_v3_prices_api.py` | DELETE 测 |
| `frontend/src/services/v3/prices.ts` | `deleteModelPrice` |
| `frontend/src/pages/ModelsPage.tsx` | 卡片内联 UI |
| `frontend/src/pages/ModelsPage.test.tsx` | vitest |

---

### Task 1: DELETE prices API

**Files:** `models_service.py`, `prices_views.py`, `urls.py`, `openapi.yaml`, `test_v3_prices_api.py`

1. 写失败测：DELETE 存在行 → 200 且库中无；DELETE 假 id → 404
2. 实现 `V3ModelsService.delete_price` + view `delete` + url `models/prices/<int:pk>/`
3. OpenAPI 补 DELETE
4. 跑通 `test_v3_prices_api`

### Task 2: ModelsPage 内联定价

**Files:** `prices.ts`, `ModelsPage.tsx`, `ModelsPage.test.tsx`

1. `deleteModelPrice(id)`；mock 进 ModelsPage test
2. 卡片：输入/输出 Input +「保存定价」；校验与 PUT/DELETE
3. vitest：回填、保存 PUT、清空 DELETE、单边空不提交
4. `npx vitest run src/pages/ModelsPage.test.tsx`

### Task 3: 验收基线（短）

写 `docs/superpowers/baselines/2026-07-24-models-inline-prices-acceptance.md`，勾选机跑结果。
