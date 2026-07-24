# P2-W2 Task 5 Review — ModelsPage 主备编辑 UI

**Reviewer:** task-scoped gate  
**Date:** 2026-07-23  
**Scope:** `ModelsPage.tsx` + `ModelsPage.test.tsx`（主备编辑 UI 增量）  
**Verdict:** Spec ✅ · Code quality **Approved**

---

## Spec compliance: ✅

| Requirement | Result |
|-------------|--------|
| 每角色主供应商下拉 | ✅ `主供应商` select + `updateRolePrimary` |
| 备选有序列表：添加 | ✅ `添加备选` select + `添加` 按钮 + `addRoleBackup` |
| 备选：上移 / 下移 | ✅ `moveRoleBackup` + `moveBackupId`；首/末项按钮 disabled |
| 备选：删除 | ✅ `removeRoleBackup` + `删除` 按钮 |
| 保存整表 PUT | ✅ `saveMappingsMutation` → `putRoleMappings({ items })` |
| PUT 含 `backup_provider_ids` | ✅ 保存时 `normalizeBackupIds` 去重保序写入 body |
| 中文文案 | ✅ `ROLE_LABEL_ZH`、主/备选/添加/上移/下移/删除/保存映射等 |
| 无 operation / recipe ID | ✅ 页面与测试均无 `operation.` / `test_model_provider` 等泄漏 |
| TDD：添加 backup 并断言 PUT body | ✅ `adds backup providers and PUTs backup_provider_ids` |
| TDD：删除 backup 并断言 PUT body | ✅ `removes a backup provider from the ordered list` |
| 类型含 `backup_provider_ids` | ✅ `domain.ts` `RoleModelMapping.backup_provider_ids?`（P2-W1 Task 5） |

**Notes:** `MAX_BACKUP_PROVIDERS = 5` 与后端 `models_service.MAX_BACKUP_PROVIDERS` 对齐；切换主供应商时 `normalizeBackupIds` 自动从备选中剔除新主 id；添加候选排除主 id 与已选备选。

---

## Code quality: Approved

主备编辑逻辑抽成纯函数（`normalizeBackupIds`、`moveBackupId`），与 `mappingDraft` 状态更新分离，可读性良好。保存路径统一 normalization，避免 PUT 携带重复 id 或与主供应商冲突。UI 在 `busy` 时禁用控件，与现有供应商 CRUD 模式一致。测试覆盖添加→排序→保存与删除→保存两条核心路径，并断言 PUT 中 `backup_provider_ids` 顺序。

---

## Findings

### Critical
*(none)*

### Important
*(none)*

### Minor

1. **测试缺口 — 切换主供应商剔除备选** — `updateRolePrimary` 会调用 `normalizeBackupIds` 移除与新主相同的备选 id，无单测覆盖。
2. **测试缺口 — 备选上限 5** — UI 在 `backups.length >= MAX_BACKUP_PROVIDERS` 时禁用添加并提示，未断言行为。
3. **测试缺口 — 重复添加同一备选** — `addRoleBackup` 对已在列表或等于主 id 的 provider 静默 no-op，未测。
4. **测试缺口 — 上移/下移边界** — 首项「上移」、末项「下移」 disabled 逻辑未单独断言（集成测试仅验证成功上移一次）。
5. **技术标识可见** — 角色行仍展示 `role_key`（如 `drama-script-writer`），非 operation ID，但与 brief「中文文案」并存；属既有模式，非本 task 回归。

---

## Strengths

- Must 五项（主/备 CRUD、PUT `backup_provider_ids`、中文、无 operation ID）均实现且有测试锚点。
- 添加/排序/删除/保存一条龙测试验证 `[backupB, backupA]` 顺序，与 UI 交互一致。
- `normalizeBackupIds` 在加载 draft、改主、添加、保存四处复用，保证前后端约束一致。
- 10 条 ModelsPage 测试 + `tsc -b` 独立复跑通过。

---

## Verification

```powershell
cd frontend
npm test -- --run src/pages/ModelsPage.test.tsx
```

**Result:** OK — 10 tests passed

```powershell
cd frontend
npm run typecheck
```

**Result:** OK

---

## Finding counts

| Severity | Count |
|----------|-------|
| Critical | 0 |
| Important | 0 |
| Minor | 5 |
