# P2-W2 Task 5 Report — ModelsPage 主备编辑 UI

**Status:** DONE  
**Date:** 2026-07-23

## Deliverables

| File | Action |
|------|--------|
| `frontend/src/pages/ModelsPage.tsx` | Modified — 主供应商下拉 + 有序备选（添加/上移/下移/删除）；PUT 含 `backup_provider_ids` |
| `frontend/src/pages/ModelsPage.test.tsx` | Modified — TDD：添加/排序/删除备选并断言 PUT body |

## Types

`RoleModelMapping.backup_provider_ids?: string[]` 已在 `domain.ts`（P2-W1 Task 5）；`putRoleMappings`/`getRoleMappings` 沿用 `RoleModelMappingTable`，无需改动。

## TDD Evidence

**RED:** 3 failed — 缺「主供应商」label /「备选供应商」UI / 删除按钮  
**GREEN:**
```powershell
cd frontend
npm test -- --run src/pages/ModelsPage.test.tsx
# Tests 10 passed
npm run typecheck
# OK
```

## Behavior

- 每角色：主供应商 select；备选有序列表（最多 5，与后端 `MAX_BACKUP_PROVIDERS` 对齐）
- 添加排除主 id 与已选备选；切换主供应商时自动从备选移除该 id
- 保存整表 PUT，`backup_provider_ids` 去重保序
- 中文文案；无 operation/recipe ID

## Commit

Skipped per instruction.
