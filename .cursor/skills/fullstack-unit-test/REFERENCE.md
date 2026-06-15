# Fullstack Unit Test — 详细参考

## 测试计划表模板

```markdown
# [模块名] 单元测试计划

**目标文件**：`apps/billing/services.py` · `BillingService.charge`
**测试文件**：`apps/billing/tests/test_charge_idempotency.py`（新建/追加）

| 用例ID | 场景类型 | 描述 | 优先级 |
|--------|----------|------|--------|
| UT-001 | 正常 | 首次扣费成功 | P0 |
| UT-002 | 边界 | 余额恰好等于 coin_cost | P0 |
| UT-003 | 异常 | 余额不足抛业务异常 | P0 |
| UT-004 | 幂等 | 相同 reference_id 只扣一次 | P0 |
| UT-005 | 权限 | 未登录 API 返回 401 | P1 |
```

场景类型：**正常**、**边界**、**异常**、**权限**、**幂等/并发**（按适用选取）。

---

## 后端：Service 层测试模板

对齐 ScriptForge 现有风格：`TestCase` + `get_user_model()` + 直接调 Service。

```python
# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.example.services import ExampleService
from apps.example.models import ExampleModel

User = get_user_model()


class ExampleServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="13800001111", password="pass")

    def test_create_success(self):
        obj = ExampleService.create(self.user, name="demo")
        self.assertEqual(obj.name, "demo")
        self.assertEqual(ExampleModel.objects.filter(user=self.user).count(), 1)

    def test_create_raises_when_name_empty(self):
        with self.assertRaises(ValueError):
            ExampleService.create(self.user, name="")
```

### 运行命令

```bash
# 单文件
python manage.py test apps.billing.tests.test_charge_idempotency

# 单类
python manage.py test apps.billing.tests.test_charge_idempotency.BillingChargeIdempotencyTests

# 单方法
python manage.py test apps.billing.tests.test_charge_idempotency.BillingChargeIdempotencyTests.test_charge_with_same_reference_only_spends_once

# 整个 app
python manage.py test apps.billing
```

---

## 后端：DRF API 测试模板

对齐项目：`APIClient` + `force_authenticate` + `resp.data["data"]`。

```python
# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

User = get_user_model()


class ExampleApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="13800002222", password="pass")
        self.admin = User.objects.create_superuser(phone="13900002222", password="admin")
        self.client = APIClient()

    def test_list_requires_auth(self):
        resp = self.client.get("/api/v1/examples/")
        self.assertEqual(resp.status_code, 401)

    def test_list_returns_data_for_owner(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get("/api/v1/examples/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("data", resp.data)

    def test_cannot_access_other_user_resource(self):
        other = User.objects.create_user(phone="13800003333", password="pass")
        self.client.force_authenticate(user=self.user)
        # 假设 obj 属于 other
        resp = self.client.get(f"/api/v1/examples/{other_obj_id}/")
        self.assertIn(resp.status_code, (403, 404))
```

### 响应体断言要点

- 成功：`self.assertEqual(resp.status_code, 200)` 且 `resp.data.get("code") == 0`（若项目统一包装）
- 分页：断言 `data` 列表 + `pagination` 字段齐全
- 校验失败：`400`，`message` 可读
- 勿断言整个大 JSON 快照（易碎）；断言关键字段存在与值

---

## 后端：查询数断言（防 N+1）

```python
from django.test import TestCase

class ExampleQueryCountTests(TestCase):
    def test_list_uses_bounded_queries(self):
        # setUp 造数 ...
        with self.assertNumQueries(3):  # 按实际调优，写入注释说明
            resp = self.client.get("/api/v1/examples/")
            self.assertEqual(resp.status_code, 200)
```

与 [fullstack-performance-tuning](../fullstack-performance-tuning/SKILL.md) 联动：优化前后更新基线数字。

---

## 后端：Mock 外部依赖

```python
from unittest.mock import patch, MagicMock

class LlmServiceTests(TestCase):
    @patch("apps.skill.services.llm_client.chat_completion")
    def test_generate_uses_mocked_llm(self, mock_chat):
        mock_chat.return_value = {"content": "{}"}
        result = SomeService.run(self.user, prompt="hi")
        self.assertTrue(result.ok)
        mock_chat.assert_called_once()
```

原则：

- patch 点在**使用处**命名空间（`where it's used`）
- 不 mock Django ORM 本身
- 网络、LLM、支付、邮件一律 mock

---

## 后端：目录与命名规范

```
apps/{app}/
├── tests/
│   ├── __init__.py
│   ├── test_{domain}_service.py   # 业务服务
│   ├── test_{domain}_api.py       # HTTP 接口
│   └── test_{feature}.py          # 特性专项（幂等、退款等）
├── services.py
└── ...
```

- 测试类：`{Feature}Tests` 或 `{Feature}ApiTests`
- 测试方法：`test_{行为}_{预期结果}`（蛇形，可读）
- 文件头：`# -*- coding: utf-8 -*-`（与现有测试一致）

---

## 前端：Vitest 最小初始化（项目尚无测试时）

仅在用户同意或明确要求时添加，最小 `package.json` 变更：

```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
```

`vite.config.js` 追加：

```js
/// <reference types="vitest" />
export default defineConfig({
  // ...existing
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.ts",
  },
});
```

`package.json` scripts：

```json
"test": "vitest run",
"test:watch": "vitest"
```

**禁止**在未确认前大规模改构建配置；优先纯函数/适配器测试（可不挂载 DOM）。

---

## 前端：工具函数 / 适配器测试

```ts
// src/services/adapters/listAdapter.test.ts
import { describe, it, expect } from "vitest";
import { parseListResponse } from "./listAdapter";

describe("parseListResponse", () => {
  it("parses standard pagination shape", () => {
    const result = parseListResponse({
      code: 0,
      data: [{ id: 1 }],
      pagination: { page: 1, page_size: 20, total: 1 },
    });
    expect(result.items).toHaveLength(1);
    expect(result.total).toBe(1);
  });

  it("returns empty list when data missing", () => {
    const result = parseListResponse({ code: 0, data: null, pagination: {} });
    expect(result.items).toEqual([]);
  });
});
```

---

## 前端：组件测试模板

```tsx
// src/components/ExampleForm.test.tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { ExampleForm } from "./ExampleForm";

describe("ExampleForm", () => {
  it("disables submit while loading", async () => {
    const onSubmit = vi.fn();
    render(<ExampleForm onSubmit={onSubmit} isLoading />);
    expect(screen.getByRole("button", { name: /提交/i })).toBeDisabled();
  });

  it("shows validation error when name empty", async () => {
    const user = userEvent.setup();
    render(<ExampleForm onSubmit={vi.fn()} />);
    await user.click(screen.getByRole("button", { name: /提交/i }));
    expect(await screen.findByText(/名称不能为空/i)).toBeInTheDocument();
  });
});
```

原则：

- 用 `getByRole` / `getByLabelText`，少依赖 class
- mock `services/api` 层，不在组件测试里打真实 HTTP
- 包裹 Router/QueryClient Provider（若组件依赖）

---

## 前端：Hook 测试

```ts
import { renderHook, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { useWorksList } from "./useWorksList";

describe("useWorksList", () => {
  it("fetches when page changes", async () => {
    const fetchWorks = vi.fn().mockResolvedValue({ items: [], total: 0 });
    const { result } = renderHook(() => useWorksList({ fetchWorks, page: 2 }));
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(fetchWorks).toHaveBeenCalledWith(expect.objectContaining({ page: 2 }));
  });
});
```

---

## 不该写 / 少写的测试

| 场景 | 建议 |
|------|------|
| 纯样式、Tailwind class | 不测 |
| 第三方库行为 | 不测 |
| 巨型 E2E 全流程 | 归 manual/E2E，非本技能重点 |
| 实现细节（私有函数） | 测公开行为 |
| 依赖真实 LLM 返回 | 必须 mock |

---

## 修改代码后的测试清单

```markdown
- [ ] 新增/更新对应用例
- [ ] `python manage.py test <path>` 通过
- [ ] `npm test` 通过（如有前端改动）
- [ ] 权限/金额类改动已补 P0 场景
- [ ] CI 可重复执行（无网络、无本地路径依赖）
```

---

## 与 fullstack-testing 映射

| 手工用例（testing） | 自动化（unit-test） |
|---------------------|---------------------|
| TC-003 缺参返回 400 | `test_create_returns_400_when_missing_field` |
| API-005 越权 | `test_cannot_access_other_user_resource` |
| SEC-AUTHZ-001 | API 权限测试同上 |
| 回归方案 P0 项 | 固化为 `manage.py test` 套件 |

手工探索性、UI 视觉、多浏览器兼容仍归 **fullstack-testing**。
