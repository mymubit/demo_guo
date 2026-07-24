# W2 Task 8 审查：幂等键 + 概览归档隐藏

**Date:** 2026-07-23  
**Scope:** `dispatcher.py`、`ProjectOverviewPage.tsx`、`test_v3_idempotency.py`（只读审查）  
**Verdict — Spec:** ✅  
**Verdict — Quality:** Approved

---

## Spec 对照

| 要求 | 结果 |
|------|------|
| `idempotency_key` 非空且同 owner+key 已有 queued/running/succeeded run → 返回已有 run | ✅ `_find_reusable_idempotent_run` + `dispatch_command` 入口短路 |
| 不双建项目 / 不双生成候选 | ✅ `test_create_project_*` / `test_generate_topic_brief_*` |
| 失败 run 不阻塞同 key 重试 | ✅ `failed` 不在可复用集合；`test_failed_run_allows_retry_*` |
| 空 key 仍新建 run | ✅ `test_empty_idempotency_key_*` |
| 已归档隐藏「归档项目」按钮 | ✅ `!project.archived_at` 条件渲染；保留「该项目已归档。」 |
| Migration `UniqueConstraint` | ⏭ 可选，未加；与失败后同 key 重试语义冲突，理由成立 |

---

## 质量备注（非阻塞）

1. **并发竞态**：先查后建，极端并发仍可能双写；W2 应用层去重可接受。
2. **幂等范围**：按 owner+key 全局匹配，未区分 `command_type`；需客户端保证 key 唯一 per 操作。
3. **测试环境**：后端需 `DRAMA_SKILLS_ROOT`（CI/本地默认路径一般可用）。

---

## 验证

```text
DRAMA_SKILLS_ROOT=... py manage.py test apps.drama.tests.test_v3_idempotency apps.drama.tests.test_v3_orchestrator --settings=config.settings.sqlite_test  → 7 passed
npm test -- src/pages/ProjectOverviewPage.test.tsx  → 5 passed
npm run typecheck  → PASS
```
