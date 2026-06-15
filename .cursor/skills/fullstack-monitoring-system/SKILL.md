---
name: fullstack-monitoring-system
description: 为 Django+DRF 后端与 React+Tailwind 前端设计并实现自研业务监控体系（不依赖 Sentry/Prometheus），覆盖采集器、慢 SQL、告警、前端 monitor SDK、管理看板与分阶段上线。适用于用户提出监控、可观测性、错误追踪、性能指标、自定义埋点、告警规则或监控看板集成时使用。
---

# Fullstack Monitoring System

## 项目基础信息

前后端分离项目：

- 后端：Django + Django REST Framework
- 前端：React + TailwindCSS + clsx + tailwind-merge + framer-motion + sonner + echarts-for-react
- 部署：Docker / docker-compose

## 需求目标

从零自研一套**全栈业务监控体系**，不引入 Sentry、Prometheus 等第三方监控成品，代码内聚在本项目内部，满足：

1. 前端自动采集：JS 报错、接口异常、页面性能指标、用户行为、路由跳转、资源加载异常
2. 后端自动采集：全局异常、接口耗时、请求入参出参、慢 SQL、日志分级、服务运行状态
3. 监控数据统一存入数据库，提供 RESTful 上报接口
4. 配套监控管理后台页面，集成进现有 React 后台系统，可查看大盘、异常列表、详情检索、筛选、趋势图表
5. 设计告警机制（可配置阈值，触发后预留扩展短信/企业微信/邮件推送入口）
6. 封装通用埋点 API，项目内所有业务代码可一行调用上报自定义事件、自定义埋点
7. 整体低侵入接入原有业务，改造量小，兼容现有业务逻辑，不破坏原有接口与页面功能

## 硬性约束

- **全程自研**：禁止集成 Sentry、Prometheus、Datadog、OpenTelemetry 等第三方监控服务。
- **低侵入**：监控失败不得影响业务请求；采集逻辑与业务逻辑解耦。
- **对齐现有栈**：优先复用项目已有 DRF 响应体、分页、权限、Axios 封装、Admin 布局与 ECharts 组件。
- **禁止随意引入新库**；确需新增依赖须说明理由与替代方案。
- **敏感数据脱敏**：password、token、authorization、cookie、secret、api_key、手机号、邮箱等字段入库前必须清洗。
- 输出默认中文；代码、表名、接口路径、字段名保持英文规范。

## 适用场景

- 新建或补全 `apps.monitoring` 后端监控 app。
- 封装或增强 `@/utils/monitor` 前端 SDK。
- 集成监控管理后台页面到现有 React Admin 路由。
- 设计告警规则、数据保留、限流防刷、灰度上线方案。
- 在业务代码中接入 `trackEvent` / `trackError` 自定义埋点。

## 分析前置步骤

动手前必须先读取现有实现（若已存在）：

**后端**

1. `backend/apps/monitoring/` — models、middleware、sql、views、services
2. `backend/config/settings/base.py` — `MONITORING_*` 配置项
3. `backend/docs/monitoring.md` — 已有 API 与接入说明
4. `backend/config/urls.py`、`apps/console/urls.py` — 路由挂载

**前端**

1. `frontend/src/utils/monitor/` — SDK 入口与 collectors
2. `frontend/src/services/http.js` — 是否已 `installAxiosMonitor`
3. `frontend/src/main.jsx` — 是否已 `initMonitor()`
4. `frontend/src/pages/Admin/monitoring/` — 后台页面
5. `frontend/src/services/api/` — `adminMonitoring` 接口封装

若项目尚无监控模块，按 [REFERENCE.md](REFERENCE.md) 从零落地；若已有部分实现，**增量扩展**而非重写。

## 工作原则

1. **监控与业务解耦**：独立 Django app + 独立前端 SDK 目录；业务代码仅调用公开 API。
2. **异步/容错写入**：存储层捕获异常并记录日志，不向上抛出影响主流程。
3. **采样与限流**：上报接口匿名可访问但 throttle；生产默认低采样起步。
4. **分层职责**：Serializer 只做校验；View 只做编排；存储/告警/脱敏下沉 `services/`。
5. **指纹去重**：异常按 fingerprint 聚合，便于列表展示与趋势统计。
6. **扩展点预留**：`send_alert()`、自定义 metric、日志检索、推送渠道对接留空实现或 stub。

## 输出要求

用户要「方案/设计」时，按以下五模块结构输出（详见 [REFERENCE.md](REFERENCE.md)）：

| 模块 | 内容 |
|------|------|
| 模块 1 | 后端监控设计：表结构、app 目录、中间件、慢 SQL、上报接口、告警、限流、API 文档 |
| 模块 2 | 前端 SDK：自动采集、手动埋点、批量上报、离线缓存、采样与白名单 |
| 模块 3 | 管理后台：大盘、异常/性能/SQL/埋点/告警页面、ECharts、权限 |
| 模块 4 | 接入与部署：初始化步骤、Docker 环境变量、灰度策略、定时清理 |
| 模块 5 | 编码约束与扩展点、完整落地顺序 |

用户要「实现代码」时：

1. 给出小步改造计划，严格按落地顺序执行。
2. 每次只改一层：先 models/migrations → services → views → SDK → 后台页面。
3. 修改后运行关联测试（如 `test_monitoring_core.py`）或说明验证步骤。
4. 涉及迁移须说明备份与回滚方案。

## 落地顺序（必须遵守）

```
Phase 0: 读取现有代码，确认增量或从零
Phase 1: 数据库表 + migrations（monitoring app）
Phase 2: 后端 services（storage/sanitizer/alerts/retention）+ middleware + sql 钩子
Phase 3: 上报接口 + 管理查询接口 + throttles + 权限
Phase 4: 前端 SDK（collectors + client + config）+ http.js 挂载 + main.jsx 初始化
Phase 5: 管理后台页面 + adminMonitoring API 封装 + 路由注册
Phase 6: 管理命令（cleanup / evaluate_alerts）+ Docker 环境变量 + 文档
Phase 7: 灰度上线（dev 关闭 → test 全量 → prod 低采样逐步放量）
```

## 快速接入清单

**前端（零改造自动采集）**

```js
// main.jsx
import { initMonitor } from '@/utils/monitor'
initMonitor()

// 登录后绑定用户（可选）
import { setMonitorUser } from '@/utils/monitor'
setMonitorUser(user)
```

**后端**

1. `INSTALLED_APPS` 注册 `apps.monitoring`
2. `MIDDLEWARE` 注册 `apps.monitoring.middleware.MonitoringRequestMiddleware`
3. 挂载 `/api/monitoring/` 与 `/api/admin/monitoring/`
4. `python manage.py migrate monitoring`

**手动埋点**

```js
import { trackEvent, trackError, trackPageView } from '@/utils/monitor'
trackEvent('export_clicked', { project_id })
trackError(error, { name: 'export_failed' })
trackPageView('/creation')
```

## 关联技能

- UI 规范：[fullstack-ui-standardization](../fullstack-ui-standardization/SKILL.md)
- 架构重构：[fullstack-refactor-plan](../fullstack-refactor-plan/SKILL.md)
- 发布部署：[fullstack-release-deploy](../fullstack-release-deploy/SKILL.md)
- 上线验证：[fullstack-testing](../fullstack-testing/SKILL.md)
- 性能优化：[fullstack-performance-tuning](../fullstack-performance-tuning/SKILL.md)

## 详细参考

- 五模块完整设计、表结构、目录、API 契约、Docker 变量：[REFERENCE.md](REFERENCE.md)
- 项目已有文档：`ScriptForge/backend/docs/monitoring.md`
