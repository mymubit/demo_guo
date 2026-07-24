### Task 8: 幂等键 + 概览小修（W1 Minor）

**Files:**
- Modify: `dispatcher.py` — 若 `idempotency_key` 非空且同 owner+key 已有成功/进行中 run，返回已有 run（不新建）
- Modify: `ProjectOverviewPage.tsx` — 已归档隐藏归档按钮
- Migration：可选 `UniqueConstraint(owner, idempotency_key)` where key != ''（若 DB 支持；SQLite 测试可用）

- [ ] **Step 1: 测试重复 idempotency_key 不双建项目/双候选**

- [ ] **Step 2–4: 实现 PASS**

---

