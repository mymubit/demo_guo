# V3 W6 套餐壳 + 删旧 + §8 全量回归验收清单（2026-07-23）

> 计划：`docs/superpowers/plans/2026-07-23-drama-website-v3-w6-billing-legacy-cut.md` Task 7  
> 设计：`docs/superpowers/specs/2026-07-22-drama-website-v3-design.md`（§8.1–8.8）  
> 前置：W0–W5 已通过（见下方基线指针）  
> 验收日：2026-07-23（Task 7 机跑复核）

## Spec §8 勾选（第一期验收）

| # | 标准（Spec §8） | 证据 | 结果 |
|---|-----------------|------|------|
| 8.1 | 原创/改编均可建项 → 选题确认 → 蓝图确认 → 分集生成 → 写满至少 1 批正文（可编辑；候选确认后才落正式版） | W1 `…-w1-shell-projects-acceptance.md`；W2 `…-w2-topic-blueprint-acceptance.md`；W3 `…-w3-episodes-scripts-acceptance.md`；本里程碑全量后端回归含 projects/topic/blueprint/episodes/scripts | ☑ |
| 8.2 | 质检：质量 + 合规双报告 → 接受问题 → 定向修订 → 报告过期语义正确 | W4 `…-w4-quality-delivery-acceptance.md`；`test_v3_quality_*` / `test_v3_accept_findings` | ☑ |
| 8.3 | 交付：双报告通过后可打包；未通过则阻断并说明原因 | W4 同上；`test_v3_delivery_gate` / `test_v3_delivery_api` | ☑ |
| 8.4 | 模型：可配置供应商与角色映射并试连成功 | W5 `…-w5-system-models-logs-acceptance.md`；`test_v3_models_api` / `test_v3_provider_test` | ☑ |
| 8.5 | 日志：任意一次生成可从项目动作追到输入 / 输出 / 校验结果 | W5 同上；`test_v3_logs_api`（generate→call 挂 `command_run`） | ☑ |
| 8.6 | 系统配置：改平台/门禁预设后，后续运行读到新配置 | W5 同上；`test_v3_system_config` / `test_v3_system_api` / quality executor 注入 | ☑ |
| 8.7 | 套餐页可展示三档文案；无支付、无配额扣减 | W6 T1–T2：`BillingPage` + `GET /api/v3/billing/plans/`；购买按钮 disabled「即将开放」；脚注无支付/配额；`BillingPage.test.tsx` | ☑ |
| 8.8 | 页面不出现 operation ID；旧 `/api/v2` 与旧 studio 路由删除或不可达 | W6 T3–T6：`/api/v2/**` → 410；`frontend/src/studio/**` 已删；v2_*/v6_*/GenerationService 已删；页面 vitest 断言无 operation/recipe ID；grep 守卫 0 匹配 | ☑ |

## 里程碑基线指针（W0–W5）

| 里程碑 | 基线路径 |
|--------|----------|
| W0 | `docs/superpowers/baselines/2026-07-22-w0-contracts-acceptance.md` |
| W1 | `docs/superpowers/baselines/2026-07-23-w1-shell-projects-acceptance.md` |
| W2 | `docs/superpowers/baselines/2026-07-23-w2-topic-blueprint-acceptance.md` |
| W3 | `docs/superpowers/baselines/2026-07-23-w3-episodes-scripts-acceptance.md` |
| W4 | `docs/superpowers/baselines/2026-07-23-w4-quality-delivery-acceptance.md` |
| W5 | `docs/superpowers/baselines/2026-07-23-w5-system-models-logs-acceptance.md` |
| W6（本文件） | `docs/superpowers/baselines/2026-07-23-w6-billing-legacy-cut-acceptance.md` |

## W6 本里程碑交付抽查

| # | 标准 | 证据 | 结果 |
|---|------|------|------|
| 1 | 三档套餐只读 API + 文案对齐 | `api/v3/billing_plans.py`；T1 report | ☑ |
| 2 | `/billing` 非占位；无购买/配额 | `BillingPage`；购买 disabled；脚注 | ☑ |
| 3 | `/api/v2/**` HTTP 410 + 引导 `/api/v3/` | `api/v2_gone.py`；`test_v2_gone` | ☑ |
| 4 | 前端 `studio/**` 删除；路由无旧入口 | T4；`router.test.tsx` | ☑ |
| 5 | 后端 v2_*/v6_*/GenerationService 删除；无假存活 import | T5；grep ZERO | ☑ |
| 6 | 旧守卫测清理为「不可达」语义 | T6；`legacy_gone` 等 | ☑ |

## 机跑回归（Task 7）

### 后端

```powershell
cd backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests --settings=config.settings.sqlite_test -v 1
```

**结果（2026-07-23）：** `Found 298 test(s)` → **Ran 298 tests in 126.645s — OK**

全量 `apps.drama.tests` 一次跑通；无需因残留 import 做排除列表。

### 前端

```bash
cd frontend
npm test
npm run typecheck
```

**结果（2026-07-23）：**

- 测试：**154 passed**（33 files）
- typecheck：`tsc -b --pretty false` → exit 0

### grep 验收

```bash
rg "v6_runtime|v6_workbench|v6_control_plane|/api/v2/studio" backend/apps/drama/orchestrator backend/apps/drama/skills_bridge backend/apps/drama/api/v3 backend/apps/drama/tasks_v3.py frontend/src/app frontend/src/pages
rg "from apps.drama.v2|GenerationService" backend/apps/drama --glob "!migrations/**"
```

**结果：** 两组均无匹配（rg exit 1 / 0 files）

## 第一期收口说明（已知延期 / 刻意不做）

以下不阻塞 W6 / Spec §8 勾选，记录为后续迭代：

| 项 | 说明 |
|----|------|
| **Tiptap / 富文本编辑器** | W3 用结构化场景 + textarea；未引入编辑器依赖 |
| **Word / PDF 导出** | W4 仅浏览器下载 JSON + Markdown |
| **真实支付 / 订阅 / 配额门禁** | 套餐页 UI only；购买按钮「即将开放」 |
| **私有部署售卖页 / 配额强制** | W6 plan 刻意不做 |
| **删 Django 旧表迁移** | 旧表可残留；产品路径不再读写 |
| **删 `drama-skills/v6/operations`** | skills 配方目录保留作内部配方源 |
| **多 Key 轮询 / failover / 成本图 / ECharts** | W5 遗留；非第一期 |
| **多人协作 / 团队权限 / 社区市场** | Spec §1.3 |
| **像素级剧本定位跳转** | W4 遗留 |

## 结论

**Spec §8.1–8.8 全部勾选；W0–W6 基线齐备；机跑后端 298 / 前端 154 + typecheck 全绿；legacy grep 清零 → W6 视为通过，V3 第一期（phase-1）收口完成。**

验收人：Task 7 agent（机跑复核，未 git commit）
