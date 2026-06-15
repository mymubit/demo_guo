# Fullstack Unit Test — 代码示例

示例对齐 ScriptForge 现有测试风格。

---

## 示例 1：Service 幂等测试（对齐 billing）

**场景**：相同 `reference_id` 扣费只执行一次。

```python
# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.billing.models import CoinLedger
from apps.billing.services import BillingService

User = get_user_model()


class BillingChargeIdempotencyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="13800009901", password="pass")
        BillingService.credit(
            self.user,
            100,
            action_key="test.grant",
            reference_id="charge-idempotency",
            remark="测试入账",
        )

    def test_charge_with_same_reference_only_spends_once(self):
        wallet = BillingService.get_or_create_wallet(self.user)
        initial_balance = wallet.balance

        BillingService.charge(
            self.user,
            "creation.submit",
            reference_id="project-1",
            coin_cost=30,
        )
        _, balance_after_duplicate = BillingService.charge(
            self.user,
            "creation.submit",
            reference_id="project-1",
            coin_cost=30,
        )

        self.assertEqual(balance_after_duplicate, initial_balance - 30)
        self.assertEqual(
            CoinLedger.objects.filter(
                user=self.user,
                action_key="creation.submit",
                reference_id="project-1",
                delta__lt=0,
            ).count(),
            1,
        )
```

**运行**：

```bash
python manage.py test apps.billing.tests.test_charge_idempotency
```

---

## 示例 2：Admin API 契约测试（对齐 console）

**场景**：管理端编排接口返回 200 且 `data` 含预期字段；废弃路由返回 404。

```python
# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

User = get_user_model()


class OrchestrationAdminApiTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            phone="13900007702",
            password="admin-pass-123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_orchestration_stats(self):
        resp = self.client.get("/api/admin/orchestration/stats/?limit=10")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("skills", resp.data["data"])

    def test_legacy_agents_prefix_deprecated(self):
        resp = self.client.get("/api/admin/agents/catalog/")
        self.assertEqual(resp.status_code, 404)
```

---

## 示例 3：用户要求「跟测」时的输出摘要

**用户输入**：`@fullstack-unit-test 我刚改了 BillingService.charge 的余额校验，补测试并跑一遍`

**Agent 输出摘要**：

```markdown
## 变更影响
- `apps/billing/services.py` → `BillingService.charge` 新增余额不足校验

## 新增用例
| 方法 | 场景 |
|------|------|
| `test_charge_raises_when_insufficient_balance` | 余额 < coin_cost 抛 `InsufficientBalance` |
| `test_charge_success_when_balance_sufficient` | 正常扣费 |

## 运行结果
\`\`\`bash
python manage.py test apps.billing.tests.test_charge_idempotency -v 2
# OK (4 tests)
\`\`\`

## 未覆盖
- 并发扣费竞态 → 建议集成测试或 `select_for_update` 专项用例
```

---

## 示例 4：前端适配器 Vitest（listAdapter）

```ts
import { describe, it, expect } from "vitest";
import { normalizeListResult } from "../listAdapter";

describe("normalizeListResult", () => {
  it("extracts items and pagination from v2 response", () => {
    const out = normalizeListResult({
      code: 0,
      data: [{ id: "a1" }],
      pagination: { page: 1, page_size: 20, total: 1, total_pages: 1 },
    });
    expect(out.items).toEqual([{ id: "a1" }]);
    expect(out.page).toBe(1);
    expect(out.total).toBe(1);
  });
});
```

---

## 示例 5：从手工用例到自动化

**fullstack-testing 手工用例**：

> API-O-003：缺少 quantity 返回 400

**fullstack-unit-test 落地**：

```python
def test_create_order_returns_400_when_quantity_missing(self):
    self.client.force_authenticate(user=self.user)
    resp = self.client.post("/api/v1/orders/", {"product_id": str(self.product.id)}, format="json")
    self.assertEqual(resp.status_code, 400)
    self.assertIn("quantity", str(resp.data).lower())
```
