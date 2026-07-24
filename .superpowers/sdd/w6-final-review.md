# W6 套餐壳 + 删旧 — 终审报告（只读）

> **审查范围：** ScriptForge V3 W6 未提交工作区  
> **对照：** `docs/superpowers/plans/2026-07-23-drama-website-v3-w6-billing-legacy-cut.md`  
> **基线：** `docs/superpowers/baselines/2026-07-23-w6-billing-legacy-cut-acceptance.md`  
> **审查日：** 2026-07-23  
> **审查方式：** 源码 spot-check + 独立 grep + 定向测试（未改 git）

---

## Strengths

1. **套餐壳实现完整且对齐计划文案**
   - `backend/apps/drama/api/v3/billing_plans.py` 三档 `basic/pro/team`、价位与 features 与计划表一致。
   - `V3BillingPlansView` 经 `GET /api/v3/billing/plans/` 返回只读 JSON；`test_v3_contract_smoke::test_billing_plans_readonly_shell` 断言 id/名称/价位。
   - OpenAPI `BillingPlan.id` enum 已更新为 `[basic, pro, team]`。

2. **BillingPage UI 符合 §8.7 语义**
   - 三卡网格、专业版 `featured`（「最受欢迎」）、按钮 `disabled` +「即将开放」、脚注「当前为展示壳，无支付与配额」。
   - `BillingPage.test.tsx` 覆盖三档渲染、推荐态、禁用购买、无 `operation.*` 暴露。
   - `/billing` 已挂入 `V3_NAV_ITEMS` / `V3Routes`；`router.test.tsx` 确认无 `/studio` 路径。

3. **旧 `/api/v2` 不可达实现正确**
   - `config/urls.py` 移除 `v2_urls` include，统一 `V2GoneView` 410（根路径 + catch-all）。
   - `api/v2_gone.py` 全 HTTP 方法返回 410，message 含 `/api/v3/`。
   - `test_v2_gone.py` + `test_v3_legacy_gone::test_v2_studio_bootstrap_returns_410` 通过。

4. **删旧范围在活代码侧基本清零**
   - 约定删除的后端模块、`frontend/src/studio/**`、旧测文件（`test_v2_studio_api` / `test_v6_runtime` / `test_generation` / `test_substance_gates_wiring`）均不存在。
   - `tasks.py` 已空壳化，无 `GenerationService` import。
   - 活代码 grep（orchestrator / skills_bridge / api/v3 / tasks_v3 / frontend pages+app）对 banned tokens **0 匹配**；`backend/apps/drama`（除 migrations）对 `from apps.drama.v2|GenerationService` **0 匹配**。

5. **守卫测试可 CI 化**
   - `test_v3_legacy_gone.py` filesystem + 路由 410 + V3 产品路径 banned token 扫描，与 W2–W5 既有 grep 测形成叠加。

6. **独立复核（本审查机跑）**
   - 后端定向 8 tests（legacy_gone + v2_gone + billing smoke）：**OK**
   - 前端 `BillingPage.test.tsx` + `router.test.tsx` 7 tests：**OK**

---

## Critical

**0 项**

产品路径（`/api/v3`、前端 pages、orchestrator）未发现：真实支付/配额扣减、v2/studio 可达、banned import 复活、UI 暴露 operation ID 等阻断性问题。

---

## Important

### I1. `scripts/verify_real_stack.py` 仍依赖已删旧栈，CI `real-celery-stack` 必炸

**位置：** `scripts/verify_real_stack.py` L24–26, L67–76  
**现象：** 仍 `import GenerationService`、`WorkflowService`（均已删除）；`docker-compose.test.yml` integration-test 最后一行仍会执行该脚本；`.github/workflows/ci.yml` 的 `real-celery-stack` job 调用 `./scripts/test-real.sh`。  
**风险：** 主单元测（298）可绿，但集成 job 在 import 阶段即 `ModuleNotFoundError`，与 W6「删旧后无半残 import」精神冲突。  
**建议：** 删除/重写为 V3 最小闭环（`tasks_v3.run_v3_command_task` + `/api/v3`），或暂时从 CI / compose 移除该 job 并文档化。

### I2. `backend/README.md` 与 W6 删旧结果相反

**位置：** `backend/README.md`（工作区已修改）  
**现象：** 文档声明「Business APIs are V2 only」、列出完整 `/api/v2/studio/**` 路由表，并引用已删的 `v2_views.py`、`v6_runtime.py`、`test_v2_studio_api`。  
**风险：**  onboarding / 运维按 README 操作会误以为 v2 仍为产品入口，直接违背 §8.8 与 W6 删旧目标。  
**建议：** 改写为 `/api/v3/` 产品 API、`/api/v2/**` 410、orchestrator/skills_bridge 边界；移除全部 v2/v6 文件引用。

---

## Minor

### M1. 导航 hint 暗示「用量」

`router.tsx` 套餐项 hint 为「方案与**用量**」，与 W6「无配额」展示壳语义略冲突。建议改为「方案与权益」类文案。

### M2. `test_v3_legacy_gone` 未自动化 frontend banned-token 扫描

计划 Task 6 / 基线 grep 包含 `frontend/src/pages` + `frontend/src/app`；守卫测仅断言 `studio/` 目录不存在，未像后端一样扫描 banned 字符串。当前人工 rg 为 0，但回归靠手动命令。

### M3. 根目录 / 品牌文档仍大量「V6 Studio」表述

`README.md` 等仍描述 V6 操作系统；不阻断 §8，但与 V3 phase-1 产品命名不一致（已知文档债）。

### M4. `skills_loader.v6_workbench` 命名保留

符合计划「允许 YAML 侧 v6_workbench 命名、禁止 import services.v6_*」；非缺陷，仅备注以免后续误删。

---

## Spec §8.7–8.8 核对

| 条款 | 要求 | 审查结论 | 证据 |
|------|------|----------|------|
| **§8.7** | 套餐页展示三档；无支付、无配额扣减 | **通过（产品路径）** | `billing_plans.py` + `BillingPage.tsx` + smoke/ vitest；无后端 quota 逻辑 |
| **§8.8** | UI 无 operation ID；旧 v2/studio 不可达 | **通过（产品路径）** | v2 → 410；`studio/**` 已删；页面 vitest 无 operation.*；活代码 grep 0 |

> 注：§8.8「删旧后文档/集成脚本不误导」见 Important I1/I2，属工程完整性而非运行时产品缺陷。

---

## 删旧范围 Checklist

| 类别 | 路径 / 行为 | 期望 | 审查 |
|------|-------------|------|------|
| 路由 | `config/urls.py` 无 `v2_urls` include | 是 | ☑ |
| 路由 | `/api/v2/**` → 410 + 引导 v3 | 是 | ☑ |
| 后端 | `v2_urls/views/serializers/service.py` | 不存在 | ☑ |
| 后端 | `services/v6_runtime|workbench|control_plane.py` | 不存在 | ☑ |
| 后端 | `services/generation_service.py` | 不存在 | ☑ |
| 后端 | `tasks.py` 无 GenerationService | 是 | ☑ |
| 前端 | `frontend/src/studio/**` | 不存在 | ☑ |
| 前端 | 无 `/studio` 路由 | 是 | ☑ |
| 旧测 | `test_v2_studio_api` / `test_v6_runtime` / `test_generation` / `test_substance_gates_wiring` | 不存在 | ☑ |
| 活代码 | orchestrator/skills_bridge/api/v3/tasks_v3 无 banned tokens | 0 匹配 | ☑ |
| 活代码 | 无 `from apps.drama.v2` / `GenerationService` import | 0 匹配 | ☑ |
| 集成 | `scripts/verify_real_stack.py` 不引用已删模块 | 否 | **☐ I1** |
| 文档 | `backend/README.md` 不描述 v2 为产品入口 | 否 | **☐ I2** |

---

## Verdict

### Ready for phase-1 close?

**No**

**理由：** Critical **0**、Important **2**（I1 集成脚本/CI、I2 后端 README 与删旧矛盾）。按审查约束「须先修复 Critical + Important」，第一期收口应暂缓，直至 I1/I2 处理完毕。

**产品/runtime 面：** W6 核心交付（套餐壳 + v2/studio 不可达 + 活代码删旧）**已达标**；阻塞项为工程/documentation/CI 尾巴，非 §8.7–8.8 运行时行为。

---

## 计数摘要

| 级别 | 数量 |
|------|------|
| Critical | **0** |
| Important | **2** |
| Minor | **4** |
| **Verdict** | **No**（phase-1 close） |

---

*审查人：Senior Code Reviewer（只读终审，未 git commit）*
