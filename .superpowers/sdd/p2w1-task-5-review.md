# P2-W1 Task 5 Review — Models API backup_provider_ids

**Reviewer:** review-agent (read-only)  
**Date:** 2026-07-23  
**Inputs:** brief, report, source + tests（review-pkg 缺失，已直接审代码）

---

## Findings

No findings.

---

## Spec Compliance

| Requirement | Verdict | Evidence |
|-------------|---------|----------|
| GET/PUT role-mappings 暴露 `backup_provider_ids` | ✅ | `models_service.py:159,184-188,225-229`；`serializers.py:231-235` |
| 校验 UUID 存在 | ✅ | `models_service.py:145-151`；`test_role_mappings_backup_provider_ids_validation` |
| 校验 ≠ 主 provider | ✅ | `models_service.py:129-134`；`test_role_mappings_primary_in_backup_rejected` |
| 去重保序 | ✅ | `models_service.py:135-138`；`test_role_mappings_backup_provider_ids_put_get` |
| 最多 5 个（`MAX_BACKUP_PROVIDERS = 5`） | ✅ | `models_service.py:15,139-144` |
| 无映射缺省 `[]` | ✅ | `models_service.py:184`；`test_role_mappings_default_includes_empty_backup_provider_ids` |
| OpenAPI 契约 | ✅ | `openapi.yaml:1564-1566`（`RoleModelMapping` 共用 GET/PUT） |
| TS 类型 | ✅ | `domain.ts:232` |
| 无 ModelsPage UI | ✅ | `ModelsPage.tsx` 无 `backup` 引用 |
| TDD RED→GREEN | ✅ | report 一致；本地复跑 10 tests OK |

---

## Quality Assessment

**Approved.**

校验集中在 `_normalize_backup_provider_ids`，与 PUT 可选字段语义（未传不覆盖，与 `temperature`/`max_tokens` 一致）清晰。测试覆盖 PUT/GET 回显、主备冲突、>5、不存在 UUID、默认空数组与去重。

### Residual risks (non-blocking)

- 未显式测 `backup_provider_ids: []` 清空已有值（代码路径正确，风险低）。
- 未传字段保留旧值行为未单测断言（与既有字段策略一致，非回归）。

### Verification

```text
Ran 10 tests in 3.656s — OK (test_v3_models_api)
```

---

## Counts

| Priority | Count |
|----------|-------|
| P0 | 0 |
| P1 | 0 |
| P2 | 0 |
| P3 | 0 |

**Spec:** ✅  
**Quality:** Approved
