### Task 6: Logs API + LogsPage 展示 failover_attempts

**Files:**
- Modify: `backend/apps/drama/api/v3/logs_views.py`（run detail）
- Modify: `docs/contracts/v3/openapi.yaml`（`LogRun` / FailoverAttempt schema）
- Modify: `frontend/src/types/v3/domain.ts`
- Modify: `frontend/src/pages/LogsPage.tsx`
- Modify: `frontend/src/pages/LogsPage.test.tsx`
- Test: 扩展 `test_v3_logs_api.py`

**API 形状：**
```json
"failover_attempts": [
  {
    "id": "uuid",
    "attempt_index": 0,
    "provider_id": "uuid",
    "provider_name": "主供应商",
    "status": "failed_switchable",
    "error_code": "http_503",
    "error_message": "…",
    "llm_call_log_id": null,
    "created_at": "ISO-8601"
  }
]
```

UI：详情抽屉「切换尝试」小节；中文状态文案；**不**渲染 operation/recipe。

- [ ] **Step 1: Failing tests** — API 含 attempts；LogsPage 在 mock detail 含 attempts 时可见「切换尝试」/供应商名

- [ ] **Step 2–4: Implement + pass**

- [ ] **Step 5: Commit** — 跳过

---
