# W5 Task 4 报告：V3RoleModelMapping + Models REST 适配层

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W5 — Providers CRUD/activate + role-mappings；复用 `LlmConfigService` / `secret_crypto`  
**Commits:** none（用户明确要求不 commit）  
**Brief:** `.superpowers/sdd/w5-task-4-brief.md`

---

## What I Implemented

### 1. Model + migration

- `V3RoleModelMapping`（`drama_v3_role_model_mapping`）：`role_key` unique、FK → `DramaLlmProvider`、`temperature`/`max_tokens` 可空、`updated_at`
- Migration：`0018_v3_role_model_mapping.py`（依赖 0017）

### 2. 适配层 `api/v3/models_service.py`

- 包装 `LlmConfigService`：list/create/get/update/delete/activate
- 响应字段：`id,name,base_url,model_name,temperature,max_tokens,is_enabled,is_active,api_key_set,remark,updated_at` — **无** `api_key`
- 空 `api_key` 走既有 `update_provider`：不覆盖密文
- 角色键 8 个（与 recipe / OpenAPI 对齐）
- GET 映射：已存行 + 缺省指向 active provider；PUT：校验 role_key + provider 后 upsert

### 3. REST `api/v3/models_views.py` + serializers + urls

| Method | Path |
|--------|------|
| GET/POST | `/api/v3/models/providers/` |
| GET/PATCH/DELETE | `/api/v3/models/providers/{id}/` |
| POST | `/api/v3/models/providers/{id}/activate/` |
| GET/PUT | `/api/v3/models/role-mappings/` |

- 信封 `{code, message, data}`；`IsAuthenticated`
- **未**实现 `…/test/`（Task 5）

### 4. 测试 `test_v3_models_api.py`（6）

创建/列表脱敏、空 key 不覆盖、唯一 activate、删除、role-mappings PUT/GET/缺省/非法 key、未登录拒绝

---

## Verification

```bash
cd backend
$env:DRAMA_SKILLS_ROOT='c:\Users\99193\Desktop\demo_guo\drama-skills'
py -3 manage.py test apps.drama.tests.test_v3_models_api -v 1 --settings=config.settings.sqlite_test
```

**结果：6/6 OK**

---

## Self-Review

- [x] Model + 0018
- [x] 复用 `LlmConfigService` / `secret_crypto`；不经 v2 视图
- [x] 永不回传 `api_key`；空 key 不覆盖
- [x] 无 `test_model_provider` / `…/test/`
- [x] 无 v6_* / 无新依赖 / 未 commit

### Concerns（非阻塞）

1. **GET 缺省映射未落库**：仅响应合成 active；executor 解析（Task 5）须同样「有行用行、无行用 active」。
2. **PUT 为 upsert 非全表替换**：未出现在 body 的既有行保留；前端若要「清空某角色」需另约定。
3. **OpenAPI create 标 200**：实现与测例均按 200；与部分 REST 惯例 201 不同，但对齐契约。

---

## Reviewer Verdict

**Spec:** ✅  
**Quality:** Approved

**Findings:** No findings.

| 必检项 | 结果 |
|--------|------|
| Providers CRUD + activate | ✅ 五路由齐全；复用 `LlmConfigService` |
| role-mappings GET/PUT | ✅ 8 键 upsert；无行缺省 active |
| 无 api_key 泄露 | ✅ `serialize_provider` 白名单 + `write_only`；空 key 不覆盖密文 |
| 测试 | ✅ 6/6 通过（独立复验） |
| 约束 | ✅ 无 `test_model_provider` / v6_* / 新依赖 |

**Residual（非阻塞）：** 未测 `GET …/providers/{id}/`、404、无 active 时 GET mappings 可能 `<8` 项；与报告 Concerns 一致，Task 5 需对齐缺省解析逻辑。
