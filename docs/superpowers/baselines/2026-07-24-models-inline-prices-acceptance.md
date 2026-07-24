# Models 内联定价验收清单（2026-07-24）

> 设计：`docs/superpowers/specs/2026-07-24-models-inline-prices-design.md`  
> 计划：`docs/superpowers/plans/2026-07-24-models-inline-prices.md`

## 验收标准

| # | 标准 | 证据 | 结果 |
|---|------|------|------|
| 1 | `DELETE /api/v3/models/prices/{id}/` 删行；缺失 404 | `test_v3_prices_api` delete 用例 | ☑ |
| 2 | PUT/GET 单价回归仍绿 | 同上 9 tests OK | ☑ |
| 3 | Models 卡片内联输入/输出 + 保存定价 | `ModelsPage` + vitest PUT 用例 | ☑ |
| 4 | 双空保存走 DELETE；单边空前端拦截 | vitest clear / half-fill | ☑ |
| 5 | OpenAPI 含 DELETE 与 Envelope | `api.test.ts` | ☑ |

## 机跑

```text
docker compose exec backend python manage.py test apps.drama.tests.test_v3_prices_api --settings=config.settings.sqlite_test -v2
# 9 OK

npx vitest run src/pages/ModelsPage.test.tsx src/types/v3/api.test.ts
# 23 passed
```

## 手检提示

1. 打开 `/models`，在供应商卡片填输入/输出单价并保存  
2. 有 token 调用后看 `/usage` 估算费用（非「未定价」）  
3. 清空两边再保存 → 回到「未定价」
