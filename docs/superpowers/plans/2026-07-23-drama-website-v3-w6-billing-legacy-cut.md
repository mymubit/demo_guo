# V3 W6 套餐壳 + 删旧 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付只读三档套餐 UI 壳（无支付/无配额），卸载并删除旧 `/api/v2/studio` 与 `frontend/src/studio/**`，删除约定的 `v2_*` / `v6_*.py` 旧编排入口，使第一期 §8 验收全绿且旧面不可达。

**Architecture:** 套餐继续走既有 `GET /api/v3/billing/plans/` 静态 JSON（对齐设计稿 §09 三档文案）。删旧采用「先不可达 → 再删文件 → 再清依赖测试」：根路由去掉 `api/v2/studio`（可选 `/api/v2/` 统一 410）；删除 `v2_*` 与 `services/v6_{runtime,workbench,control_plane}.py`；同步删除仅服务旧栈的 `GenerationService` 任务链与相关测试，避免半残 import。V3 `/api/v3` + `orchestrator` + `skills_bridge` 为唯一产品路径。

**Tech Stack:** 同 W5；不引入支付 SDK；不引入新第三方库。

**Spec:** `docs/superpowers/specs/2026-07-22-drama-website-v3-design.md`（§8 项 7–8；里程碑 W6）  
**Roadmap:** `docs/superpowers/plans/2026-07-22-drama-website-v3.md`  
**Prerequisite:** W5 已通过（`docs/superpowers/baselines/2026-07-23-w5-system-models-logs-acceptance.md`）

## 产品语义（Global）

### 套餐壳（无支付）

- 三档对齐设计稿 HTML §09（**覆盖**当前 `BILLING_PLANS` 中「免费/专业/团队」旧文案）：

| id | name | price_label | 要点 features（中文，可略压缩） |
|----|------|-------------|--------------------------------|
| `basic` | 基础版 | `¥99/月` | 每月 3 项目；每项目最多 30 集；基础评分/合规；标准导出；不含分镜/宣发/API |
| `pro` | 专业版 | `¥299/月` | 每月 10 项目；最多 100 集；十维评分；合规+修复；分批+质检闭环；分镜+宣发；不含团队协作 |
| `team` | 团队版 | `¥999/月` | 不限项目/集数；自定义权重；企业合规库；5 席位协作；完整交付包；API；客成 |

- UI：`/billing` 三卡展示；可标「专业版」推荐；**无**「立即购买 / 支付 / 升级扣费」真实动作（按钮可灰显文案「即将开放」或纯展示）
- **禁止**配额校验、扣减、支付回调

### 删旧范围（锁定）

**必须删除或不可达：**

| 区域 | 路径 |
|------|------|
| 路由 | `backend/config/urls.py` 中 `api/v2/studio/` include |
| 后端模块 | `v2_urls.py` / `v2_views.py` / `v2_serializers.py` / `v2_service.py` |
| V6 编排入口 | `services/v6_runtime.py` / `v6_workbench.py` / `v6_control_plane.py` |
| 前端 | `frontend/src/studio/**`（含 `studio-contract.test.ts`） |
| 旧测 | `test_v2_studio_api.py` / `test_v6_runtime.py` |

**随 v6/v2 删除的死链（必须一并处理，禁止留半残 import）：**

| 区域 | 说明 |
|------|------|
| `services/generation_service.py` | 仅旧 job 主路径依赖 `V6Runtime` → **删除**或移入 `_legacy/` 且无任何 import（推荐直接删） |
| `tasks.py` 中调用 `GenerationService` 的 Celery 任务 | 删除或改为空 stub 并保证无调度入口；保留文件名若 Celery 发现需要，但函数体不得 import 已删模块 |
| `tests/test_generation.py` / `test_substance_gates_wiring.py` | 依赖 GenerationService → **删除**或改写为仅测仍存活的纯函数（优先删除） |

**明确保留（不是 W6 删除目标）：**

- `drama-skills/v6/operations/**` 配方包（skills 真相源）
- `skills_loader` 读取 skills 清单的方法（可仍名含 v6_workbench YAML，但**禁止** import `apps.drama.services.v6_*`）
- `tasks_v3.py`、V3 orchestrator、全部 `/api/v3`
- 旧 Django 模型表（`DramaProject` 等）可留库不删迁移；W6 不做数据迁移清理

### 不可达验收

- `GET/POST /api/v2/studio/**` → **404 或 410**（推荐：根路由挂 `path("api/v2/", V2GoneView)` 统一 410 + 中文「旧接口已下线，请使用 /api/v3/」）
- 前端无 `/studio` 路由；`V3_NAV_PATHS` 不含 studio
- `rg` 于 `backend/apps/drama/orchestrator`、`skills_bridge`、`api/v3`、`frontend/src/pages`、`frontend/src/app`：**0** 匹配 `v6_runtime|v6_workbench|v6_control_plane|/api/v2/studio`

## Global Constraints

- 创作者 UI 禁止暴露 `operation.*` / 配方 ID
- **禁止**支付、配额扣减、真实计费
- **禁止**往已删的 v2/v6 加功能；删完后不得复活 import
- 不引入新第三方库
- Commit 仅在用户明确要求时执行（计划 Commit 步骤默认 **跳过**）
- 工作目录：`c:\Users\99193\Desktop\demo_guo`
- 后端：`py -3 manage.py test … --settings=config.settings.sqlite_test`
- `DRAMA_SKILLS_ROOT` → 仓库 `drama-skills`

## File Map

| 职责 | 路径 |
|------|------|
| 套餐文案 | `api/v3/views.py` `BILLING_PLANS` 或抽 `billing/plans.py` |
| 套餐 UI | `pages/BillingPage.tsx`、`services/v3/billing.ts` |
| 下线 | `config/urls.py` + 可选 `api/v2_gone.py` |
| 删除 | `v2_*`、`services/v6_*.py`、`frontend/src/studio/**`、旧测、`generation_service` 链 |
| 回归 | W0–W5 测试套件 + 新 unreachability 测 + §8 清单基线 |

## W6 验收标准

1. `/billing` 展示三档（基础/专业/团队）文案与价位，对齐设计稿；无支付/配额
2. `/api/v3/billing/plans/` 返回同上三档；契约/冒烟绿
3. `/api/v2/studio/**` 不可达（410/404）；无 studio 前端路由
4. 约定删除文件不存在；活代码无 `apps.drama.services.v6_*` / `v2_*` import
5. W0–W5 回归全绿；新增删旧/套餐测全绿
6. Spec §8 项 1–8 在基线文档勾选（引用既有里程碑证据 + 本里程碑证据）

---

### Task 1: 套餐文案对齐 HTML + 契约/冒烟

**Files:**
- Modify: `api/v3/views.py`（或抽出 `api/v3/billing_plans.py`）— 重写 `BILLING_PLANS`
- Modify: `docs/contracts/v3/openapi.yaml` 示例（若有）与 `test_v3_contract_smoke.py`
- Optional TS: `types/v3/domain.ts` BillingPlan 已有则对齐 id 枚举注释

```python
BILLING_PLANS = [
    {"id": "basic", "name": "基础版", "price_label": "¥99/月", "features": [...]},
    {"id": "pro", "name": "专业版", "price_label": "¥299/月", "features": [...]},
    {"id": "team", "name": "团队版", "price_label": "¥999/月", "features": [...]},
]
```

- [ ] **Step 1: 失败测** — smoke 断言三 id + 价位字符串
- [ ] **Step 2: 改文案**
- [ ] **Step 3: 测绿**
- [ ] **Step 4: Commit**（跳过）

---

### Task 2: BillingPage UI

**Files:**
- Rewrite: `pages/BillingPage.tsx`、`services/v3/billing.ts`、`BillingPage.test.tsx`
- UI：三卡；专业版可 `featured` 样式；脚注「当前为展示壳，无支付与配额」；无购买提交
- 无 operation ID；无新依赖

- [ ] **Step 1–4: TDD + typecheck**

---

### Task 3: `/api/v2` 不可达

**Files:**
- Modify: `backend/config/urls.py` — 移除 `include("apps.drama.v2_urls")`
- Create: 简单 `V2GoneView`（APIView get/post/put/patch/delete → 410 + `{code,message,data}` 或项目统一信封）挂 `path("api/v2/", ...)` 与 `path("api/v2/<path:rest>", ...)`
- Test: `test_v2_gone.py` — `/api/v2/studio/bootstrap/` → 410；断言 message 含「/api/v3」
- 更新 urls 注释（去掉「V6 Studio 是唯一业务入口」）

- [ ] **Step 1–3: TDD**
- [ ] **Step 4: Commit**（跳过）

---

### Task 4: 删除前端 `studio/**`

**Files:**
- Delete: `frontend/src/studio/**` 全部
- Grep `frontend/src` 确保无残留 import；修 `router` / 测试若有引用
- 确认 `App` / `router` 无 `/studio` Route（W0 已无则仅删目录）

- [ ] **Step 1: 删除 + grep 清零**
- [ ] **Step 2: `npm test` 相关 + typecheck**
- [ ] **Step 3: Commit**（跳过）

---

### Task 5: 删除后端 `v2_*` + 旧 Generation/V6 入口

**顺序（必须）：**

1. 确认 Task 3 已让路由不 include `v2_urls`
2. Delete: `v2_urls.py` `v2_views.py` `v2_serializers.py` `v2_service.py`
3. Delete: `services/v6_runtime.py` `v6_workbench.py` `v6_control_plane.py`
4. Delete: `services/generation_service.py`（若仍存在）
5. 清理 `tasks.py`：删除/改写所有 `GenerationService` 调用；保留模块可加载
6. Delete tests: `test_v2_studio_api.py` `test_v6_runtime.py` `test_generation.py` `test_substance_gates_wiring.py`（若仅测旧链）
7. Grep `backend/apps/drama`（除 migrations / drama-skills 引用说明外）无：
   - `from apps.drama.v2`
   - `apps.drama.services.v6_runtime`
   - `apps.drama.services.v6_workbench`
   - `apps.drama.services.v6_control_plane`
   - `GenerationService`

若 `generation_gate.py` 等仍被 V3 误引用：先确认无 import，再删或保留纯函数。

- [ ] **Step 1: 删文件**
- [ ] **Step 2: 修断链至 import 清零**
- [ ] **Step 3: `manage.py check` + 相关 test 发现不再收集旧模块**
- [ ] **Step 4: Commit**（跳过）

---

### Task 6: 删旧守卫测 + CI 友好断言

**Files:**
- Create/extend: `test_v3_legacy_gone.py`（或扩 `test_v3_async_commands` 的 grep 测）
  - 文件系统：上述删除路径 `assertFalse(Path(...).exists())`
  - 路由：v2 → 410
  - 源码扫描：orchestrator / skills_bridge / api/v3 / tasks_v3 无 banned 字符串
- 前端：`router.test.tsx` 已有 not studio；可加 `Billing` 路径仍在

- [ ] **Step 1–3: TDD**
- [ ] **Step 4: Commit**（跳过）

---

### Task 7: §8 全量回归基线

**Files:**
- Create: `docs/superpowers/baselines/2026-07-23-w6-billing-legacy-cut-acceptance.md`
- Modify: roadmap W6 ✅；标注第一期完成

**机跑（实际执行，模块列表按仓库现状调整）：**

```bash
cd backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests --settings=config.settings.sqlite_test -v 1
# 若全量 apps.drama.tests 含不应跑的残留，改为显式 W0–W6 模块列表

cd frontend
npm test
npm run typecheck
```

```bash
rg "v6_runtime|v6_workbench|v6_control_plane|/api/v2/studio" backend/apps/drama/orchestrator backend/apps/drama/skills_bridge backend/apps/drama/api/v3 backend/apps/drama/tasks_v3.py frontend/src/app frontend/src/pages
rg "from apps.drama.v2|GenerationService" backend/apps/drama --glob "!migrations/**"
```

基线勾选 Spec §8.1–8.8，引用 W0–W5 基线路径 + 本里程碑证据。

- [ ] **Step 1: 机跑写入基线**
- [ ] **Step 2: 勾选 §8**
- [ ] **Step 3: 第一期收口说明（已知延期：Tiptap、Word/PDF、支付等）**

---

## Self-Review（计划作者）

| Spec | Task |
|------|------|
| §8.7 三档套餐无支付 | T1–T2 |
| §8.8 v2/studio 不可达 + 无 operation ID | T3–T6 |
| 删除 v2_* / v6_* / studio | T4–T5 |
| 全绿回归 | T7 |

**风险：** 删除 `GenerationService` 可能牵出更多冷门 import——Task 5 以 grep 清零为完成条件，禁止留 `try/except ImportError` 假存活。

**刻意不做：** 真实支付、配额门禁、私有部署售卖页、删 Django 旧表迁移、删 `drama-skills/v6/operations`。
