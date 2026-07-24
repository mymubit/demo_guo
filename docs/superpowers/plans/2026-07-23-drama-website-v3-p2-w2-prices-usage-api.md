# V3 P2-W2 主备 UI + 单价 + 日 rollup + Usage API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: `superpowers:subagent-driven-development`. Continuous execution — do not pause for human confirmation between tasks. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Models 页可编辑角色主备链；落地 `V3ModelPrice` + `V3UsageDailyRollup`；提供 Prices REST 与 `GET /api/v3/usage/summary/`。不含 `/usage` 页与 ECharts（P2-W3）。

**Architecture:** 成功/失败 call log 落库后同步增量更新日 rollup（Asia/Shanghai）；费用用单价表估算；ModelsPage 扩展 `backup_provider_ids` 编辑（上移/下移/添加/删除）。

**Tech Stack:** 同 P2-W1；无新第三方库；无 ECharts。

**Spec:** `docs/superpowers/specs/2026-07-23-drama-website-v3-phase2-failover-usage-design.md` §4.3–4.4、§6 prices/usage、§7 ModelsPage  
**Roadmap:** `docs/superpowers/plans/2026-07-23-drama-website-v3-phase2.md`  
**Prerequisite:** P2-W1 ✅

## Global Constraints

- 创作者 UI 禁止暴露 operation/recipe ID
- 禁止 v2/v6_runtime 加功能
- mock 测试；禁止外网
- **不**引入 ECharts；**不**新建 UsagePage（W3）
- rollup `date` = **Asia/Shanghai** 日历日
- 必须有 `unpriced_call_count`
- Commit 默认跳过
- 工作目录：`c:\Users\99193\Desktop\demo_guo`
- `py -3 manage.py test … --settings=config.settings.sqlite_test`
- `DRAMA_SKILLS_ROOT` → 仓库 `drama-skills`

## File Map

| 职责 | 路径 |
|------|------|
| 单价/rollup 模型 | `models.py` + migration `0021_…` |
| rollup 写入 | `orchestrator/usage_rollup.py` |
| 挂接 call log | `llm_call_log_service.py` 或 router/executor 成功路径后 |
| Prices API | `api/v3/prices_views.py` + urls |
| Usage API | `api/v3/usage_views.py` + urls |
| OpenAPI/TS | `openapi.yaml`、`types/v3/domain.ts`、`services/v3/*` |
| Models UI | `ModelsPage.tsx` + test |
| 测试 | `test_v3_model_price*`、`test_v3_usage_rollup*`、`test_v3_prices_api*`、`test_v3_usage_api*` |

---

### Task 1: V3ModelPrice 模型

**Files:** Modify `models.py`; Create migration `0021_v3_model_price.py`; Test `test_v3_model_price.py`

**Produces:** `V3ModelPrice` per Spec §4.3；`unique_together (provider, model_name)`；Decimal fields。

- [ ] TDD: create price row → unique conflict on duplicate
- [ ] Implement + migrate
- [ ] Commit 跳过

---

### Task 2: V3UsageDailyRollup + increment helper

**Files:** `models.py` + same or `0022` migration；Create `orchestrator/usage_rollup.py`；Test `test_v3_usage_rollup.py`

**Produces:**
```python
def shanghai_date(dt) -> date: ...
def estimate_cost(*, provider_id, model_name, prompt_tokens, completion_tokens) -> Decimal | None: ...
def apply_call_to_rollup(call_log: DramaLlmCallLog) -> None:
    """按 Asia/Shanghai 日 + owner/project/command_type/model/provider 维度 upsert 累加。
    无单价：estimated_cost 不加，unpriced_call_count += 1。
    command_type 从 call.v3_command_run.command_type 取（可空）。
    provider_id：能从 base_url/model 反查则填，否则空。
    """
```

Wire: after `DramaLlmCallLog` create/save in `llm_call_log_service` (or equivalent single write path), call `apply_call_to_rollup`. Keep sync (no Celery required for W2).

- [ ] TDD: priced call increments cost；unpriced increments unpriced_call_count；same-day upsert
- [ ] Implement
- [ ] Commit 跳过

---

### Task 3: Prices API GET/PUT

**Files:** `api/v3/prices_views.py`、`serializers`、`urls.py`、OpenAPI、TS、`services/v3/prices.ts`；Test `test_v3_prices_api.py`

**Contract:**
- `GET /api/v3/models/prices/` → `{ items: [{ id, provider_id, provider_name, model_name, price_in_per_1k, price_out_per_1k, currency }] }`
- `PUT /api/v3/models/prices/` body `{ items: [...] }` 全量 upsert（按 provider_id+model_name）；校验 provider 存在、价格 ≥0

- [ ] TDD API
- [ ] Implement
- [ ] Commit 跳过

---

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

### Task 5: ModelsPage 主备编辑 UI

**Files:** `ModelsPage.tsx`、`ModelsPage.test.tsx`；ensure `getRoleMappings`/`putRoleMappings` types include `backup_provider_ids`

**UI:** 每个角色：主 provider 下拉 + 备选列表（添加下拉、上移、下移、删除）；保存 PUT 整表；中文文案；无 operation ID。

- [ ] TDD: 可添加 backup 并 PUT 含 backup_provider_ids
- [ ] Implement
- [ ] Commit 跳过

---

### Task 6: P2-W2 验收基线

**Files:** `docs/superpowers/baselines/2026-07-23-p2-w2-prices-usage-api-acceptance.md`；update phase2 roadmap

机跑：
```powershell
py -3 manage.py test apps.drama.tests.test_v3_model_price apps.drama.tests.test_v3_usage_rollup apps.drama.tests.test_v3_prices_api apps.drama.tests.test_v3_usage_api apps.drama.tests.test_v3_models_api --settings=config.settings.sqlite_test -v 1
```
```bash
cd frontend && npm test -- --run src/pages/ModelsPage.test.tsx && npm run typecheck
```

验收项：单价 CRUD；rollup 增量与 unpriced；usage summary owner 隔离；Models 备选 UI；无 ECharts/UsagePage。

- [ ] 全绿 + 写基线 + roadmap ✅
- [ ] Commit 跳过

---

## Spec coverage

| Spec | Task |
|------|------|
| §4.3 V3ModelPrice | T1 |
| §4.4 rollup + unpriced | T2 |
| §6 prices | T3 |
| §6 usage summary | T4 |
| §7 Models 主备 UI | T5 |
| W2 验收 | T6 |
| /usage + ECharts | W3 |

## Execution

Continuous SDD；用户已授权中间不停顿确认。
