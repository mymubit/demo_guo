# 独立剧本评审 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans`。按任务逐步执行；每任务以测试门禁结束。未要求不 commit。

**Goal:** 交付全局「剧本评审」：外界剧本粘贴/上传 → 质量评分 + 合规审查 → 历史记录 → 同 kind 两条并排对比；可可选关联项目。

**Architecture:** 新域 `ScriptReview` / `ScriptReviewRun`；API `/api/v3/reviews/`；执行时把 `script_text` 包装成临时 scripts 形态复用 scorer/compliance 配方，**不写**项目 `V3ArtifactVersion`；前端一级导航 `/reviews`。

**Tech Stack:** Django/DRF/Celery、既有 skills_bridge + LlmProvider、React Query、Vitest、Django TestCase（LLM mock）。

**Spec:** `docs/superpowers/specs/2026-07-24-standalone-script-review-design.md`

## Global Constraints

- 响应信封 `{ code: 0, message, data }`
- 仅 owner 可访问；关联 `project_id` 须属当前用户
- 上传仅 `.txt`/`.md`，建议 ≤2MB；不做 `.docx`
- 不写入项目 quality/compliance artifact；不影响交付门禁
- 对比要求同 `kind` 且均 `succeeded`
- 中文 UI；测试默认普通逻辑 ≥5 case / 高风险 ≥12

## File map

| 文件 | 职责 |
|------|------|
| `backend/apps/drama/models.py` | `ScriptReview` / `ScriptReviewRun` |
| `backend/apps/drama/migrations/0027_*.py` | 迁移 |
| `backend/apps/drama/services/script_review_service.py` | CRUD、包装脚本、触发评分/合规、对比投影 |
| `backend/apps/drama/orchestrator/` 或 `skills_bridge/` | 桥接异步执行（新建 command types 或内部 runner） |
| `backend/apps/drama/api/v3/reviews_views.py` + `urls.py` | REST |
| `backend/apps/drama/api/v3/serializers.py` | 入参校验 |
| `docs/contracts/v3/openapi.yaml` | 契约 |
| `backend/apps/drama/tests/test_v3_script_review*.py` | API/执行测 |
| `frontend/src/types/v3/domain.ts` | TS 类型 |
| `frontend/src/services/v3/reviews.ts` | API client |
| `frontend/src/pages/ScriptReviewsPage.tsx` 等 | 列表/新建/详情/对比 |
| `frontend/src/app/router.tsx` | 导航 + 路由 |
| `frontend/src/pages/QualityPage.tsx` | 「用外界剧本评分」入口 |

---

### Task 1: 模型 + migration

**Files:** `models.py`, `migrations/0027_script_review.py`, `test_v3_script_review_models.py`

- [ ] 写测：创建 Review + Run；owner/project 可空关联
- [ ] 实现 `ScriptReview` / `ScriptReviewRun` + migrate
- [ ] `docker compose exec backend python manage.py migrate`

### Task 2: CRUD API

**Files:** `script_review_service.py`, `reviews_views.py`, `serializers.py`, `urls.py`, `openapi.yaml`, `test_v3_script_review_api.py`

- [ ] 测：POST paste 创建、multipart 上传 txt、列表仅本人、GET 详情、非法扩展名 400、他人 404
- [ ] 实现 GET/POST `/reviews/`、GET `/reviews/{id}/`
- [ ] OpenAPI 补 schemas + paths

### Task 3: 异步评分 / 合规

**Files:** `script_review_service.py`, dispatcher/recipe 或专用 runner, `test_v3_script_review_async.py`

- [ ] 测：mock LLM 后 `POST .../score/` → run succeeded + `report_payload`；compliance 同理；失败写 failed
- [ ] 新增命令类型或内部任务：`score_external_script` / `check_external_compliance`（产品命令名可中文化展示）
- [ ] 包装 `script_text` → 临时 scripts 输入；**断言**无新 V3ArtifactVersion quality/compliance
- [ ] 轮询：前端用 run status 或挂既有 command_run

**命令建议（契约）：**

| command_type | 说明 |
|--------------|------|
| `score_external_script` | 外界质量评分 |
| `check_external_compliance` | 外界合规审查 |

### Task 4: runs 列表 + compare API

**Files:** service + views + tests

- [ ] 测：runs 列表、同 kind 对比 200、不同 kind / 未成功 400
- [ ] `GET .../runs/`、`GET .../runs/{id}/`、`GET .../compare/?a=&b=`

### Task 5: 前端壳 + 列表/新建

**Files:** `domain.ts`, `reviews.ts`, `ScriptReviewsPage.tsx`, `ScriptReviewNewPage.tsx`, `router.tsx`, tests

- [ ] 导航增加「剧本评审」
- [ ] 列表 + 新建（粘贴/上传 Tab）
- [ ] vitest：列表空态、创建调用

### Task 6: 详情 + 触发评分 + 对比页

**Files:** `ScriptReviewDetailPage.tsx`, `ScriptReviewComparePage.tsx`, Quality 入口, tests

- [ ] 详情：预览、评分/合规按钮、runs 表、多选对比
- [ ] 对比页左右栏
- [ ] QualityPage 链到 `/reviews/new?project_id=`
- [ ] vitest：触发 score、对比导航

### Task 7: 验收基线

写 `docs/superpowers/baselines/2026-07-24-standalone-script-review-acceptance.md`，勾选机跑结果。

---

## 执行方式

用户确认 plan 后：

1. **Subagent-Driven** — 每任务子代理  
2. **Inline** — 本会话连续做完  

默认若用户说「继续/开干」→ Inline 从 Task 1 起。
