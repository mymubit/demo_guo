# P2-W1 Task 5 Report — Models API 暴露 backup_provider_ids

**Status:** DONE  
**Date:** 2026-07-23  
**Scope:** GET/PUT `/api/v3/models/role-mappings/` 序列化 + 校验；OpenAPI + TS 类型；无 UI

---

## Deliverables

| File | Action |
|------|--------|
| `backend/apps/drama/api/v3/serializers.py` | `RoleModelMappingItemSerializer` 增加 `backup_provider_ids` |
| `backend/apps/drama/api/v3/models_service.py` | `MAX_BACKUP_PROVIDERS=5`；`_normalize_backup_provider_ids`；serialize/put/default |
| `backend/apps/drama/tests/test_v3_models_api.py` | +4 tests（PUT/GET、主 id 冲突、>5/不存在、默认 `[]`） |
| `docs/contracts/v3/openapi.yaml` | `RoleModelMapping.backup_provider_ids` |
| `frontend/src/types/v3/domain.ts` | `RoleModelMapping.backup_provider_ids?: string[]` |

---

## TDD Evidence

### Step 1 — RED

```powershell
cd c:\Users\99193\Desktop\demo_guo\backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_models_api --settings=config.settings.sqlite_test -v 1
```

**Result:** FAIL — `KeyError: 'backup_provider_ids'`；主 id 入 backup / >5 未拒（200）

### Step 2 — Implementation

- GET 回显 `backup_provider_ids`（无映射缺省 `[]`）
- PUT 可选字段；校验 UUID 存在、≠ 主 provider、去重保序、≤5
- 主 id 出现在 backup → 400

### Step 3 — GREEN

同 RED 命令：**OK — Ran 10 tests**

---

## Self-Review

| Check | Result |
|-------|--------|
| PUT 带 backups，GET 同列表 | ✓ |
| 主 provider 在 backup → 400 | ✓ |
| >5 / 不存在 UUID → 400 | ✓ |
| 去重保序 | ✓ |
| 无 ModelsPage UI | ✓ |
| 未 git commit | ✓ |

**Concerns:** PUT 未传 `backup_provider_ids` 时不覆盖已有值（与 temperature/max_tokens 一致）；前端 UI 留 W2。
