### Task 5: Models API 暴露 backup_provider_ids（无 UI）

**Files:**
- Modify: `backend/apps/drama/api/v3/serializers.py`（`RoleModelMappingItemSerializer`）
- Modify: `backend/apps/drama/api/v3/models_service.py`（serialize + put 校验）
- Modify: `docs/contracts/v3/openapi.yaml`（role-mappings schema）
- Modify: `frontend/src/types/v3/domain.ts`（若已有 Mapping 类型）
- Test: 扩展 `test_v3_models_api.py`

**规则：**
- PUT item 可含 `backup_provider_ids: string[]`
- 校验：UUID 存在、≠ 主 provider、去重保序、最多 5 个（写死常量 `MAX_BACKUP_PROVIDERS = 5`）
- GET 回显同字段

- [ ] **Step 1: Failing API test** — PUT 带 backups，GET 见同一列表；主 id 出现在 backup → 400

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Implement**

- [ ] **Step 4: Run — OK**

- [ ] **Step 5: Commit** — 跳过

---
