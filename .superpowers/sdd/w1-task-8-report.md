# W1 Task 8 报告：W1 验收基线

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W1 — W1 验收基线  
**W1 结论:** **通过**  
**Commits:** none

---

## What I Did

1. 创建 `docs/superpowers/baselines/2026-07-23-w1-shell-projects-acceptance.md` — 逐条勾选 W1 验收标准 6 项并附命令/路径证据
2. 更新 `docs/superpowers/plans/2026-07-22-drama-website-v3.md` — W1 行标记 ✅ 并指向 acceptance baseline
3. 顺带修正 `frontend/index.html` 标题：`ScriptForge Studio · V6` → `ScriptForge · 短剧剧本创作一体机`（与 LoginPage 品牌一致）

---

## Verification（Task 8 Step 2 回归）

**后端：**

```bash
cd backend
py -3 manage.py test apps.drama.tests.test_v3_contract_smoke apps.drama.tests.test_v3_domain_w1 apps.drama.tests.test_v3_orchestrator apps.drama.tests.test_v3_projects_crud -v 1 --settings=config.settings.sqlite_test
```

→ **Ran 14 tests in 7.664s — OK**

**前端：**

```bash
cd frontend
npm test -- src/types/v3/api.test.ts src/app/router.test.tsx src/services/v3/projects.test.ts src/pages/DashboardPage.test.tsx
npm run typecheck
```

→ **11 passed**（4 files）；typecheck exit 0

---

## W1 验收标准勾选摘要

| # | 标准 | 结果 |
|---|------|------|
| 1 | 仪表盘列表 / 新建 / 进入项目 | ☑ |
| 2 | 归档 + 默认隐藏 + 显示已归档 | ☑ |
| 3 | commands create_project 同步；异步/未知不调 LLM | ☑ |
| 4 | 项目概览 stage/entry_type/选题定调 CTA | ☑ |
| 5 | V3_NAV 单一来源；Login 无 Studio 黑话 | ☑ |
| 6 | W0 冒烟 + W1 新增测试全绿 | ☑ |

---

## Concerns

1. 无阻塞项。异步创作命令仍为 `unsupported` 桩，属 W1 设计预期，W2 再实现。
2. 旧 studio/v2 代码路径仍存在于仓库，W6 删除；不影响 W1 验收范围。

---

## Files Touched

- `docs/superpowers/baselines/2026-07-23-w1-shell-projects-acceptance.md`（新建）
- `docs/superpowers/plans/2026-07-22-drama-website-v3.md`（W1 行 ✅）
- `frontend/index.html`（标题修正）
- `.superpowers/sdd/w1-task-8-report.md`（本文件）
