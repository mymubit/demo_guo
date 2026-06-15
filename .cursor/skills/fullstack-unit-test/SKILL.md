---
name: fullstack-unit-test
description: 为 Django+DRF 后端与 React+Tailwind 前端编写可执行的自动化单元测试与接口测试代码，覆盖 services 层、Serializer 校验、API 契约、权限边界与前端组件/Hook 逻辑。适用于用户提出补单元测试、写 pytest/Django TestCase、API 测试、Vitest 测试、测试覆盖率提升或修改后关联测试时使用。
---

# Fullstack Unit Test

## 项目基础信息

- 前后端分离 Web 网站（flickplay / ScriptForge）
- 后端：Django + Django REST Framework
- 前端：React + Vite + TailwindCSS + TanStack Query + Zustand
- **后端现状**：`apps/{app}/tests/test_*.py`，以 `django.test.TestCase` + `rest_framework.test.APIClient` 为主，业务逻辑优先测 `services.py`
- **前端现状**：尚未接入测试 runner；新增前端测试默认 **Vitest + @testing-library/react**（须先确认或最小化初始化）
- 规范对齐：`.cursor/rules/security-testing-standards.mdc`、`django-backend-standards.mdc`

## 适用场景

当用户提出以下需求时使用本技能：

- 为 `services.py`、Serializer、View/ViewSet 补充 Django 单元/接口测试
- 为 React 组件、自定义 Hook、工具函数、适配器编写 Vitest 测试
- 修改代码后补关联测试并执行 `manage.py test` / `npm test`
- 提升核心模块（金额、订单、权限、配置）测试覆盖率
- 用 `assertNumQueries` 等断言防止 N+1 回归

与其他技能分工：

- **本技能**：编写并运行**自动化测试代码**
- [fullstack-testing](../fullstack-testing/SKILL.md)：手工用例与回归方案（非自动化代码）
- [fullstack-bidirectional-review](../fullstack-bidirectional-review/SKILL.md)：评审建议补测，不直接写测试
- [fullstack-performance-tuning](../fullstack-performance-tuning/SKILL.md)：性能优化后用 `assertNumQueries` 等固化回归
- [fullstack-api-alignment](../fullstack-api-alignment/SKILL.md)：契约变更时同步更新 API 测试断言

## 工作原则

1. **先读现有测试**：对齐同 app 命名、setUp、断言风格，不引入冲突框架
2. **测行为不测实现**：关注输入输出、权限、边界、异常，不绑定私有方法细节
3. **隔离外部依赖**：LLM、支付、第三方 HTTP 必须 mock；单测不依赖外部网络
4. **数据库**：后端用 Django 测试库；禁止连生产库
5. 普通逻辑覆盖**正常、边界、异常、非法输入、权限**；金额/订单/权限类 ≥ 更完整用例
6. 改代码后**必须运行**关联测试；不能运行时说明原因与剩余风险
7. 禁止随意引入新测试库；前端 Vitest 初始化须最小 diff 并说明
8. 输出默认中文；测试代码、路径、类名保持英文

## 工作流程

```
1. 确认范围 → 目标文件/函数/接口 + 是否含权限/金额/并发
2. 读取上下文 → 现有 tests/、services、Serializer、fixtures 模式
3. 选定层级 → service 单测 / API 集成 / 前端组件或 Hook
4. 编写测试 → 命名清晰、单一断言主题、可重复执行
5. 运行验证 → manage.py test 或 npm test，修复失败
6. 输出摘要 → 新增用例列表、覆盖场景、运行命令
```

## 测试分层速查

| 层级 | 工具 | 适用 | 项目路径惯例 |
|------|------|------|--------------|
| Service 单测 | `TestCase` | 业务逻辑、事务、幂等 | `apps/{app}/tests/test_*_service.py` |
| API 集成 | `APIClient` | 状态码、响应体、权限 | `apps/{app}/tests/test_*_api.py` |
| Serializer | `TestCase` | 字段校验、write_only | 可与 service 同文件或独立 |
| ORM/Model | `TestCase` | 约束、自定义 save | 少量，优先 service |
| React 组件 | Vitest + RTL | 渲染、交互、条件分支 | `src/**/*.test.tsx` |
| Hook/工具 | Vitest | 纯函数、状态逻辑 | `src/**/*.test.ts` |
| 适配器 | Vitest | 分页/字段解析 | `src/services/**/*.test.ts` |

## 输出要求

### 用户要「补测试」时

1. 测试计划表：用例 ID、场景类型、目标函数/接口
2. 完整可运行测试代码（含 import、setUp）
3. 运行命令与预期结果
4. 未覆盖风险（需集成测试/E2E 的部分）

### 用户粘贴改动要求「跟测」时

1. 分析改动影响的函数/接口
2. 新增或更新对应用例
3. 运行测试并报告通过/失败

完整模板与示例见 [REFERENCE.md](REFERENCE.md)、[examples.md](examples.md)。

## 分析前置步骤

动手前优先读取：

**后端**

1. 同 app `tests/` 下已有文件与基类用法
2. 目标 `services.py`、`serializers.py`、`views.py`
3. 统一响应格式（如 `{ code, message, data }`）与权限类
4. `manage.py test` 常用参数与 CI 是否已配置

**前端**

1. `package.json` 是否已有 `vitest` / `jest` 脚本
2. 目标组件、Hook、`services/` 适配器
3. 是否已有 `setupTests` 或 `vitest.config`

## 优先级（先测什么）

| 等级 | 模块类型 | 说明 |
|------|----------|------|
| P0 | 金额、订单、扣费、权限、鉴权 | 必须有用例 |
| P1 | Serializer 校验、分页、配置读写 | 契约易碎 |
| P2 | 工具函数、适配器、纯展示组件 | 性价比高 |
| P3 | 样式、动效 | 通常不单测 |

## 详细参考

- 后端/前端模板、mock 规范、命令速查：[REFERENCE.md](REFERENCE.md)
- 完整代码示例：[examples.md](examples.md)
