# W0 Task 6 报告：W0 验收清单

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W0 — W0 验收清单  
**Commits:** none（按指令未提交）

---

## Note on Brief

`.superpowers/sdd/w0-task-6-brief.md` 不存在；按  
`docs/superpowers/plans/2026-07-22-drama-website-v3-w0-contracts.md` Task 6 执行。

---

## Deliverable

创建 `docs/superpowers/baselines/2026-07-22-w0-contracts-acceptance.md`，含计划要求的 6 行验收表 + 附加复核与结论。

---

## Verification Performed（本 Task 实时复核）

### 1. 契约文档存在性

| 路径 | 状态 |
|------|------|
| `docs/contracts/v3/glossary.md` | 存在 — 8 行术语表 + 禁止对用户说列 |
| `docs/contracts/v3/commands.md` | 存在 — 15 条 command_type |
| `docs/contracts/v3/openapi.yaml` | 存在 — projects + billing paths |

### 2. 前端测试

```text
> npm test -- src/app/router.test.tsx src/types/v3/api.test.ts

 ✓ src/types/v3/api.test.ts (1 test)
 ✓ src/app/router.test.tsx (1 test)

 Test Files  2 passed (2)
      Tests  2 passed (2)
```

```text
> npm run typecheck

（exit 0）
```

### 3. 后端冒烟测试

```text
> py -3 manage.py test apps.drama.tests.test_v3_contract_smoke -v 2 --settings=config.settings.sqlite_test

test_billing_plans_readonly_shell ... ok
test_create_project_returns_summary ... ok
test_list_projects_envelope ... ok

Ran 3 tests in 1.094s
OK
```

（注：本环境 `python` 不可用，需用 `py -3`。）

### 4. 前端无 /studio 路由

| 检查点 | 结果 |
|--------|------|
| `App.tsx` grep `studio` | 无匹配 |
| `router.tsx` grep `studio` | 无匹配 |
| `V3_NAV_PATHS` | `/dashboard`、`/models`、`/logs`、`/system`、`/billing` |
| `router.test.tsx` | 断言无 `/studio` 前缀 — PASS |

### 5. 占位页文案（operation.* 抽查）

| 页面 | 标题 | operation.* |
|------|------|-------------|
| DashboardPage | 创作仪表盘 | 无 |
| ModelsPage | 模型配置 | 无 |
| LogsPage | 执行日志 | 无 |
| SystemPage | 系统配置 | 无 |
| BillingPage | 套餐 | 无 |
| ProjectOverviewPage | 项目概览 | 无 |
| AppShell 导航 | 中文五项 | 无 |

### 6. 跨 Task 证据链

| Task | 报告 | 关键产出 |
|------|------|----------|
| 1 | `w0-task-1-report.md` | glossary + commands |
| 2 | `w0-task-2-report.md` | openapi.yaml |
| 3 | `w0-task-3-report.md` | TS types + api.test.ts |
| 4 | `w0-task-4-report.md` | `/api/v3` 空壳 + smoke 3/3 |
| 5 | `w0-task-5-report.md` | V3Routes 壳 + router.test |

---

## Acceptance Checklist Summary

| 项 | 结果 |
|----|------|
| glossary + commands 存在 | ☑ |
| openapi.yaml 含 projects/billing | ☑ |
| TS 命令枚举测试绿 | ☑ |
| test_v3_contract_smoke 绿 | ☑ |
| 前端无 /studio 路由 | ☑ |
| 创作者文案无 operation.*（占位页） | ☑ |

**W0 判定：通过**

---

## Concerns / Carry-forward

1. **LoginPage 英文遗留**：侧栏含「Studio V6」「Operation graph / trace ledger …」「V6 runtime ready」。登录跳转已是 `/dashboard`，不违反路由契约；建议 W1 统一 V3 中文品牌，非 W0 阻塞项。
2. **`frontend/src/studio/**` 目录**：物理文件仍在，但 `App.tsx` 已无 import；W6 计划物理删除。
3. **未 git commit**：全 W0 工作树变更仍待用户决定是否提交。

---

## Files Created

| 路径 | 说明 |
|------|------|
| `docs/superpowers/baselines/2026-07-22-w0-contracts-acceptance.md` | W0 验收 baseline |
| `.superpowers/sdd/w0-task-6-report.md` | 本报告 |
