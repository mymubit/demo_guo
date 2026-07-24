### Task 4: Usage summary API

**Files:** `api/v3/usage_views.py`、urls、OpenAPI、TS、`services/v3/usage.ts`；Test `test_v3_usage_api.py`

**Contract:**
`GET /api/v3/usage/summary/?project_id=&date_from=&date_to=&group_by=day|model|command_type&live=0|1`

Response:
```json
{
  "timezone": "Asia/Shanghai",
  "date_from": "...",
  "date_to": "...",
  "group_by": "day",
  "rows": [
    {
      "key": "2026-07-23",
      "prompt_tokens": 0,
      "completion_tokens": 0,
      "total_tokens": 0,
      "call_count": 0,
      "success_count": 0,
      "estimated_cost": "0.00",
      "unpriced_call_count": 0
    }
  ],
  "totals": { "...same metrics..." }
}
```

- Default read rollup；`live=1` merge last 6 hours from call logs (optional minimal: if live=1, recompute window from call logs only for that window — keep simple).
- Owner isolation: only current user's data.

- [ ] TDD
- [ ] Implement
- [ ] Commit 跳过

---
