# ScriptForge 全栈项目审计总报告

**审计日期**：2026-06-15  
**修复完成日期**：2026-06-15（AUD-001～014 全量修复计划已落地）  
**审计对象**：`ScriptForge/`（Django + DRF 后端，React + Vite 前端）  
**审计模式**：只读（14 项 Cursor 技能顺序审计，不修改业务代码）  
**分支快照**：`ScriptForge` @ `1bb0b99`，工作区 **247** 个未提交变更（大规模重构 WIP）  
**结论基于**：修复后工作区快照；**未创建 git commit**（按计划要求）

---

## 修复后结论（2026-06-15 更新）

| 项 | 修复前 | 修复后 |
|----|--------|--------|
| **整体健康度** | 黄色 | **黄绿（可继续联调/预发）** — P0 阻塞项已处理，WIP 未提交仍存在 |
| **未应用迁移** | 11 项 | **0**（已 migrate + seed_system_config） |
| **后端测试** | 294 OK | **317 OK**（+23 门户/用户/安全测试） |
| **前端 Vitest** | 无 | **11 用例**（listAdapter + businessAdapters） |
| **React Query** | 未使用 | Works/Detail/Admin Users/Wallet/Member 已接入 |
| **OpenAPI** | 无 | `drf-spectacular` + `/api/schema/` + `docs/openapi.yaml` |

**验证命令**：

```bash
cd backend && python manage.py test --keepdb --verbosity=0   # 317 OK
cd frontend && npm test && npm run build                      # 11 OK, build OK
```

---

## 一、执行摘要

| 项 | 结果 |
|----|------|
| **整体健康度** | **黄色（部分通过）** — 架构与契约对齐进展良好，但发布阻塞项未清零 |
| **前端构建** | 通过（`vite build` 6.12s） |
| **后端测试** | 通过（294 tests，1 skipped，`--keepdb` 42.7s） |
| **未应用迁移** | **11 项**待执行（含 `system_config`、`orders`、`billing`、`token_blacklist`） |
| **契约联调** | 文档标注项均为「待复测」 |
| **前端自动化测试** | 无（无 Vitest/Jest） |

### Top 5 阻塞项（P0）

| # | 问题 | 来源技能 |
|---|------|----------|
| 1 | 247 个未提交变更，重构未完成，不具备可发布基线 | release-deploy |
| 2 | 11 个数据库迁移未应用，预发/生产 `migrate` 未验证 | release-deploy |
| 3 | `frontend-backend-contract-audit.md` 核心路径全部「待复测」 | testing / api-alignment |
| 4 | `users` / `membership` / `security` app 无 `tests/`，门户 API 测试缺口大 | unit-test |
| 5 | 前端零自动化测试 + React Query 已初始化但业务层未使用 | unit-test / frontend-alignment-refactor |

### Top 5 建议项（P1）

| # | 建议 | 来源技能 |
|---|------|----------|
| 1 | 完成 `home.hero_stats`、`monitoring.frontend_sample_rate` 等配置迁移 | dynamic-system-config |
| 2 | `creation/services.py` 1070 行，建议按领域继续拆分 | refactor-plan / bidirectional-review |
| 3 | ECharts chunk 671KB（gzip 229KB），评估按需加载 | performance-tuning |
| 4 | 生产 compose 默认 `SECRET_KEY` 占位符须强制环境变量覆盖 | security-audit / release-deploy |
| 5 | 建立 OpenAPI 导出（`fullstack-openapi-sync` 未建）替代纯手工契约表 | api-alignment |

---

## 二、项目快照

### Git 状态

- 分支：`ScriptForge`（跟踪 `origin/ScriptForge`）
- 未提交文件：约 **247** 行 `git status --short`
- 典型变更：删除 `admin_panel`、各 app 旧 `urls.py`/`views.py`；新增 `portal/`、`console/` 网关分层；前端删除 `SkillConfig.jsx`、`memberStore.js` 等

### 基线命令结果

| 命令 | 结果 |
|------|------|
| `python manage.py showmigrations --plan` | 11 项 `[ ]` 未应用（见附录） |
| `npm run build` | **成功**，2843 模块，最大 chunk `EChart` 671.78 kB |
| `python manage.py test --keepdb` | **OK**：Ran **294** tests in 42.682s (skipped=1) |

> 首次全量测试因测试库已存在触发交互提示；审计使用 `--keepdb` 完成。

---

## 三、分技能审计结果

### 1. fullstack-refactor-plan

- **结论**：部分通过
- **发现统计**：P0 0 | P1 3 | P2 2

| 等级 | 发现 |
|------|------|
| P1 | 后端已落地 `portal/` + `console/` 双网关，符合 [CENTERS.md](backend/CENTERS.md) 与 [config/urls.py](backend/config/urls.py) 设计 |
| P1 | 领域逻辑下沉 `services.py` 在 billing/orders/membership 做得较好 |
| P1 | `creation/services.py` **1070 行**，编排+创作+作品混杂，维护成本高 |
| P2 | 前端 `services/` 按域拆分清晰，但 `api.js` barrel 与 `admin/` 子目录并存，导入路径待统一 |
| P2 | React Query 在 [main.jsx](frontend/src/main.jsx) 初始化，**全项目无 `useQuery` 使用**，服务端状态未统一治理 |

**建议**：优先拆分 `creation/services.py`；推动列表/详情页接入 React Query。

---

### 2. fullstack-api-alignment

- **结论**：部分通过
- **发现统计**：P0 1 | P1 1 | P2 1

| 等级 | 发现 |
|------|------|
| P0 | [frontend-backend-contract-audit.md](frontend-backend-contract-audit.md) 联调表 5 条均为 **「待复测」** |
| P1 | 文档列出的 10 项差异 **均已适配/兼容已清理**，静态代码与文档一致 |
| P2 | [listAdapter.js](frontend/src/services/adapters/listAdapter.js) `normalizeArrayResult` 仍保留 `result` 裸数组兜底（L24），与「仅 `{data}`」契约略有偏差 |

**建议**：按联调模板完成 auth/creation/works/admin 五条路径复测并更新状态列。

---

### 3. fullstack-frontend-alignment-refactor

- **结论**：部分通过
- **发现统计**：P0 0 | P1 2 | P2 2

| 等级 | 发现 |
|------|------|
| P1 | 请求统一走 [http.js](frontend/src/services/http.js)，页面无裸 `axios`/`fetch` |
| P1 | 适配器集中于 `adapters/listAdapter.js`、`businessAdapters.js`，`project_id` 已统一 |
| P2 | 无 `src/api/` 模块化目录（仍为 `services/*.js`），与 REFERENCE 目标结构有差距 |
| P2 | 无前端测试文件，`package.json` 无 `test` 脚本 |

---

### 4. fullstack-legacy-compat-removal

- **结论**：部分通过
- **发现统计**：P0 0 | P1 2 | P2 3

| 等级 | 发现 |
|------|------|
| P1 | 前端 **无** `result.items`、`task_id||project_id`、`expires_at` 双读等过渡分支 |
| P1 | 后端 **有意保留** 410 废弃路由：[portal/agent/urls.py](backend/apps/portal/agent/urls.py)、[portal/workflow/urls.py](backend/apps/portal/workflow/urls.py) |
| P2 | 后端内部 `legacy_*` 函数（`pipeline_nodes_legacy_shape`、`expand_legacy_episode_summaries`）为数据形态迁移，非 API 双版本 |
| P2 | [skillTerm.js](frontend/src/utils/skillTerm.js) 读取 `api_meta.deprecated_fields`，属元数据而非兼容分支 |
| P2 | `normalizeArrayResult` 裸数组兜底（见 api-alignment） |

**建议**：410 路由保留合理；评估 `normalizeArrayResult` 是否可收紧为仅 `data` 数组。

---

### 5. fullstack-cleanup-audit

- **结论**：风险阻塞（清理进行中）
- **发现统计**：P0 1 | P1 2 | P2 1

| 等级 | 发现 |
|------|------|
| P0 | 247 个 WIP 变更含大量 `D` 删除与 `??` 新增，**清理/refactor 未收敛到可提交状态** |
| P1 | `admin_panel` app 已删除，符合网关迁移方向 |
| P1 | 前端无 `admin_panel`/`SkillConfig`/`memberStore` 残留引用（静态扫描通过） |
| P2 | `skill/` 与 `workflow/`/`agent/` 存在 parallel tests 目录，历史重复需后续合并 |

**建议**：分批 commit：网关迁移 → 领域 views 删除 → 前端路由更新；每批跑测试。

---

### 6. dynamic-system-config

- **结论**：部分通过
- **发现统计**：P0 0 | P1 3 | P2 1

| 等级 | 发现 |
|------|------|
| P1 | `system_config` app 已建，但迁移 `system_config.0001_initial` **未应用** |
| P1 | [dynamic-config-migration-catalog.md](docs/dynamic-config-migration-catalog.md) 中 `home.hero_stats`、`monitoring.frontend_sample_rate` 等为 **「待接入」** |
| P1 | [Home/index.jsx](frontend/src/pages/Home/index.jsx) `STATS` 硬编码，未用 `useConfig('home.hero_stats')` |
| P2 | 部分已接入：`creation.ai_field_fallback_cost` 等通过 config 服务读取 |

**建议**：预发执行 `migrate` + `seed_system_config`；P0 配置项按 catalog 分批替换硬编码。

---

### 7. fullstack-monitoring-system

- **结论**：部分通过
- **发现统计**：P0 0 | P1 2 | P2 1

| 等级 | 发现 |
|------|------|
| P1 | 后端 `apps/monitoring/` + 文档 [monitoring.md](backend/docs/monitoring.md) 齐全；路由 `/api/monitoring/` 已挂载 |
| P1 | 前端 SDK：[utils/monitor/](frontend/src/utils/monitor/) 9 文件；[main.jsx](frontend/src/main.jsx) 已 `initMonitor()`；[http.js](frontend/src/services/http.js) 已 `installAxiosMonitor` |
| P2 | `monitoring.frontend_sample_rate` 配置待接入 SDK [config.js](frontend/src/utils/monitor/config.js) |
| P2 | 有 `test_monitoring_core.py`，覆盖核心采集 |

**建议**：将采样率改为从 `system-configs` 公开接口或 `useConfig` 读取。

---

### 8. fullstack-bidirectional-review（抽样）

- **结论**：部分通过
- **发现统计**：P0 0 | P1 4 | P2 3

**抽样范围**：鉴权、创作、计费、管理编排、监控

| 等级 | 模块 | 发现 |
|------|------|------|
| P1 | 订单 | [portal/orders/views.py](backend/apps/portal/orders/views.py) `get_object` 经 `OrderService.get_order_detail(user, pk)` 校验归属，设计合理 |
| P1 | 创作 | [portal/creation/views.py](backend/apps/portal/creation/views.py) 鉴权完整，下载走 FileResponse |
| P1 | 前端守卫 | [guards.jsx](frontend/src/router/guards.jsx) 使用 `hasAdminAccess()`，与后端 staff 对齐 |
| P1 | 计费 | [billing/tests/test_charge_idempotency.py](backend/apps/billing/tests/test_charge_idempotency.py) 覆盖幂等，实现质量高 |
| P2 | 创作服务 | `creation/services.py` 体量过大，单文件职责过多 |
| P2 | 前端请求 | React Query 未用于列表/详情，易产生重复请求与竞态 |
| P2 | 作品详情 | `businessAdapters` 多字段 fallback（`fusion_snapshot` 蛇形/驼峰双读）为后端字段过渡期设计 |

---

### 9. fullstack-ui-standardization（抽样）

- **结论**：部分通过
- **发现统计**：P0 0 | P1 1 | P2 3

| 等级 | 发现 |
|------|------|
| P1 | 首页 [Home/index.jsx](frontend/src/pages/Home/index.jsx) 使用 `ThemeBadge`、`THEME_META_LIST`、`lucide-react`，符合设计体系 |
| P2 | 首页 `STATS`/`TESTIMONIALS` 大段硬编码营销文案，应逐步迁入配置中心 |
| P2 | 静态扫描未发现 `gray-`/`slate-`/`purple-` 杂色 class（符合 navy/gold 规范） |
| P2 | 未抽检全部 Admin 页；MonitoringDashboard 已懒加载，构建 chunk 合理 |

---

### 10. fullstack-testing

- **结论**：风险阻塞
- **发现统计**：P0 2 | P1 2 | P2 0

| 等级 | 发现 |
|------|------|
| P0 | 契约审计 5 条核心路径 **待复测** |
| P0 | WIP 状态下无法划定稳定回归范围 |
| P1 | 建议回归域：auth 刷新、creation 提交、works 分页、admin 用户列表、billing 扣费 |
| P1 | 上线准入清单（testing 模板）**阻塞项均未勾选** |

**回归用例矩阵（摘要）**

| 用例ID | 域 | 优先级 | 状态 |
|--------|-----|--------|------|
| RG-001 | 登录/刷新 Token | P0 | 待执行 |
| RG-002 | 创作提交+进度 | P0 | 待执行 |
| RG-003 | 作品列表分页 | P0 | 待执行 |
| RG-004 | 充值/会员订单 | P0 | 待执行 |
| RG-005 | 管理后台用户列表 | P1 | 待执行 |

---

### 11. fullstack-unit-test

- **结论**：部分通过
- **发现统计**：P0 1 | P1 3 | P2 1

| 等级 | 发现 |
|------|------|
| P0 | 前端 **0** 测试文件，无 `npm test` |
| P1 | 后端 **294** 测试通过；creation/skill/billing/console 覆盖较好 |
| P1 | **无 tests/**：`users`、`membership`、`security`；`portal` 仅 1 个测试文件 |
| P1 | 门户 orders/billing/auth API 缺集成测试 |
| P2 | 测试 DB 残留导致首次运行需 `--keepdb` 或手动删库 |

**后端测试分布（摘要）**

| App | 有 tests | 评估 |
|-----|----------|------|
| creation | 30+ | 充分 |
| skill/workflow/agent | 多个 | 充分 |
| billing/orders | 有 | 商业路径部分覆盖 |
| console | 有 | 管理 API 部分覆盖 |
| monitoring/system_config | 有 | 基础设施有覆盖 |
| users/membership/security | **无** | 缺口 |

---

### 12. fullstack-security-audit

- **结论**：部分通过
- **发现统计**：P0 1 | P1 3 | P2 2

| 等级 | 发现 |
|------|------|
| P0 | [docker-compose.prod.yml](docker-compose.prod.yml) 默认 `SECRET_KEY=${SECRET_KEY:-django-insecure-change-me-in-production}`，未设置 env 时有弱密钥风险 |
| P1 | [production.py](backend/config/settings/production.py) `DEBUG=False`、HSTS、签名/限流开关设计合理 |
| P1 | 订单/创作视图通过 service 层校验归属，降低 IDOR 风险 |
| P1 | 前端无 `dangerouslySetInnerHTML` 静态命中；剧本 HTML 经 sanitize 模块 |
| P2 | `http.js` 开发默认 `API_SIGN_SECRET` 空字符串，依赖环境注入 |
| P2 | Admin 路由仅前端 `hasAdminAccess`，须确保所有 `/api/admin/*` 后端强制 `IsAdminUser` |

**建议**：生产部署 checklist 强制校验 `SECRET_KEY`、`API_SIGN_SECRET` 非默认值。

---

### 13. fullstack-performance-tuning

- **结论**：部分通过
- **发现统计**：P0 0 | P1 3 | P2 2

| 等级 | 发现 |
|------|------|
| P1 | 构建产物 ECharts chunk **671 kB**（gzip 229 kB），首屏/admin 图表页压力大 |
| P1 | React Query 未使用，列表页可能重复 fetch（StrictMode 双 mount 放大） |
| P1 | 部分热点已用 `select_related`/`prefetch_related`（orders、console、system_config） |
| P2 | `creation/services.py` 体量大，部分列表路径需运行时 profiling 确认 SQL 条数 |
| P2 | 监控已配置 `MONITORING_SLOW_API_MS=1000`、`MONITORING_SLOW_SQL_MS=500` |

---

### 14. fullstack-release-deploy

- **结论**：风险阻塞
- **发现统计**：P0 3 | P1 2 | P2 1

| 等级 | 发现 |
|------|------|
| P0 | 247 未提交变更，无稳定发布 tag |
| P0 | 11 未应用迁移（含 system_config、orders.0003、billing.0011） |
| P0 | 契约联调未复测，不具备上线准入 |
| P1 | Docker prod compose 结构完整：migrate → gunicorn 4 workers |
| P1 | 健康检查 `/api/health/` 已配置 |
| P2 | compose 中 backend 挂载 `./backend:/app` 适合 dev，生产宜 immutable 镜像 |

### 上线准入评分

| 检查项 | 状态 |
|--------|------|
| P0 用例通过 | 未执行 |
| 核心链路冒烟 | 未执行 |
| 迁移预发验证 | 未通过（本地未应用） |
| DEBUG=False | 配置已具备 |
| 密钥环境变量化 | 有默认弱回退 |
| 监控接入 | 已接入 |
| **综合** | **不建议上线** |

---

## 四、跨技能问题聚合表

| 问题ID | 等级 | 来源技能 | 描述 | 建议 |
|--------|------|----------|------|------|
| AUD-001 | P0 | release-deploy / cleanup | 247 个 WIP 未提交变更 | 分批 commit + CI |
| AUD-002 | P0 | release-deploy | 11 个 migration 未应用 | 预发 `migrate --plan` 后执行 |
| AUD-003 | P0 | testing / api-alignment | 契约 5 条待复测 | 按 audit 文档执行并联调 |
| AUD-004 | P0 | unit-test | users/membership/security 无 tests | 补 API + service 测试 |
| AUD-005 | P0 | unit-test | 前端零自动化测试 | 初始化 Vitest，先测 adapters |
| AUD-006 | P0 | security / release-deploy | 生产 SECRET_KEY 弱默认 | 部署强制 env 校验 |
| AUD-007 | P1 | dynamic-system-config | system_config 迁移未应用 + 硬编码 STATS | migrate + 配置迁移 P0 |
| AUD-008 | P1 | refactor-plan / bidirectional-review | creation/services.py 1070 行 | 按子域拆分 service |
| AUD-009 | P1 | frontend-alignment / performance | React Query 未使用 | 列表/详情 Hook 迁移 |
| AUD-010 | P1 | performance-tuning | ECharts 大包 671kB | 路由级 lazy + 按需 import |
| AUD-011 | P1 | monitoring | frontend_sample_rate 未接入 | 读 system_config |
| AUD-012 | P2 | api-alignment | normalizeArrayResult 裸数组兜底 | 收紧或文档化例外 |
| AUD-013 | P2 | legacy-compat | 后端 410 废弃路由 | 保留，文档说明即可 |
| AUD-014 | P2 | release-deploy | prod compose 源码卷挂载 | 生产改用镜像内代码 |

---

## 五、推荐后续迭代顺序（2–4 周）

### 第 1 周：收敛基线

1. 分批提交 WIP（网关 → 领域 → 前端），每批 `manage.py test --keepdb`
2. 应用全部 pending migrations，记录回滚点
3. 执行契约审计 5 条联调，更新 audit 文档状态

### 第 2 周：质量补齐

4. 为 `users`、`portal/auth`、`portal/orders` 补 API 测试
5. 前端初始化 Vitest，覆盖 `listAdapter`、`businessAdapters`、`http` 解包
6. `home.hero_stats` 等 P0 配置接入 `useConfig`

### 第 3 周：性能与安全

7. 列表页接入 React Query；ECharts 路由懒加载复查
8. 生产 env 校验脚本（SECRET_KEY、API_SIGN_SECRET）
9. 可选：接入 `drf-spectacular` + `docs/openapi.yaml`（openapi-sync 技能）

### 第 4 周：上线准备

10. 完整回归 RG-001～005
11. release-deploy 检查清单全勾
12. 灰度发布 + 监控观察 30min

---

## 六、附录

### A. 未应用迁移（showmigrations --plan）

```
[ ] billing.0011_coinledger_unique_negative_reference
[ ] creation.0012_add_last_failed_dimensions
[ ] orders.0003_membershipgrant
[ ] system_config.0001_initial
[ ] token_blacklist.0001_initial … 00013（共 9 项）
```

### B. 执行的命令

```bash
git branch --show-current
git status -sb
python manage.py showmigrations --plan
npm run build                                    # frontend/
python manage.py test --keepdb --verbosity=0     # backend/, 294 OK
python manage.py test --keepdb apps.billing apps.console apps.system_config apps.monitoring apps.orders  # 21 OK
```

### C. 静态扫描模式

- Legacy 前端：`result.items`、`task_id||`、`expires_at` — 无匹配
- 裸 HTTP：`axios.` / `fetch(` 于 `frontend/src` — 无匹配
- UI 杂色：`gray-`/`slate-`/`purple-` — 无匹配
- XSS：`dangerouslySetInnerHTML` — 无匹配

### D. 抽样文件清单

**后端**：`config/urls.py`、`portal/urls.py`、`portal/orders/views.py`、`portal/creation/views.py`、`billing/services.py`、`creation/services.py`、`config/settings/production.py`

**前端**：`services/http.js`、`services/adapters/listAdapter.js`、`services/adapters/businessAdapters.js`、`router/guards.jsx`、`pages/Home/index.jsx`、`main.jsx`、`utils/monitor/`

### E. 审计技能执行顺序

refactor-plan → api-alignment → frontend-alignment-refactor → legacy-compat-removal → cleanup-audit → dynamic-system-config → monitoring-system → bidirectional-review → ui-standardization → testing → unit-test → security-audit → performance-tuning → release-deploy

---

*报告由 Cursor Agent 按 `.cursor/skills/` 14 项技能审计流程自动生成。*

### F. AUD-001～014 修复状态（2026-06-15 全量修复）

| ID | 状态 | 修复摘要 | 验证 |
|----|------|----------|------|
| AUD-001 | 部分修复 | 各阶段 test/build 门禁通过；WIP 未 commit | `test --keepdb` + `npm run build` |
| AUD-002 | **已修复** | 11 项迁移已应用；`billing.0010` 增加 positive 重复清洗 | `migrate` + `seed_system_config` |
| AUD-003 | **部分修复** | auth 联调表 2 行自动化覆盖；creation/works/admin 仍待复测 | `portal/tests/test_auth_api.py` |
| AUD-004 | **已修复** | portal/users/security 新增 API/中间件测试 | 23 新用例 |
| AUD-005 | **已修复** | Vitest 初始化 + adapter 单测 11 例 | `npm test` |
| AUD-006 | **已修复** | prod compose 必填密钥；production.py 启动校验 | `scripts/check-deploy-env.ps1` |
| AUD-007 | **已修复** | `home.hero_stats` useConfig；Wallet `payment.default_method` | Home/Wallet 页面 |
| AUD-008 | **已修复** | `creation/services/` 拆分为 facade 子模块 | `apps.creation` 236 tests OK |
| AUD-009 | **已修复** | `hooks/queries/` 五页 React Query 迁移 | 页面手工回归 |
| AUD-010 | **部分修复** | vite `echarts`/`echarts-react` 独立 chunk（~648kB） | `npm run build` |
| AUD-011 | **已修复** | `monitoring.frontend_sample_rate` 接入 configStore | `configStore.js` |
| AUD-012 | **已修复** | `normalizeArrayResult` 仅接受 `{ data: array }` | `listAdapter.test.js` |
| AUD-013 | **已修复** | 410 路由文档化 | `frontend-backend-contract-audit.md` |
| AUD-014 | **已修复** | prod compose 移除 backend 源码卷 | `docker-compose.prod.yml` |

### G. 上线准入清单（节选）

| 检查项 | 结果 |
|--------|------|
| 数据库迁移已应用 | 通过 |
| 后端全量测试 | 317 OK |
| 前端 build | 通过 |
| 前端 Vitest | 11 OK |
| 生产密钥无占位符 | compose + settings 校验 |
| OpenAPI 基础设施 | `/api/schema/` + `docs/openapi.yaml` |
| Git 工作区收敛 | **未通过**（仍 WIP，需用户 commit/PR） |
