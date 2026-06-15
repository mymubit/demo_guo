# 全栈业务监控体系 — 完整参考

## 模块 1：后端监控设计（Django）

### 1.1 数据库表结构

独立 Django app：`apps.monitoring`。所有表显式 `db_table`，前缀建议 `{project}_`（如 `sf_`）。

| 模型 | 表名 | 用途 |
|------|------|------|
| `MonitoringException` | `sf_monitoring_exception` | 前后端异常统一记录 |
| `ApiPerformanceLog` | `sf_api_performance_log` | 接口耗时与请求上下文 |
| `FrontendEvent` | `sf_frontend_event` | 前端埋点/性能/行为事件 |
| `SqlPerformanceLog` | `sf_sql_performance_log` | 慢 SQL 记录 |
| `AlertRule` | `sf_alert_rule` | 告警阈值配置 |
| `AlertEvent` | `sf_alert_event` | 告警触发记录 |
| `ServiceHealthSnapshot` | `sf_service_health_snapshot` | 服务健康快照 |

**MonitoringException 核心字段**

- `source`: `frontend` | `backend`
- `level`: `debug/info/warning/error/critical`
- `exception_type`, `message`, `stack`
- `path`, `method`, `status_code`
- `user_id`, `ip_address`, `user_agent`, `trace_id`
- `fingerprint`: SHA256 聚合键（type + message + path）
- `request_data`, `response_data`, `extra` (JSON，已脱敏)
- `created_at` (indexed)

**ApiPerformanceLog 核心字段**

- `path`, `method`, `status_code`, `duration_ms`
- `query_count`, `slow_sql_count`
- `request_size`, `response_size`
- `user_id`, `trace_id`, `request_data`, `response_data`, `extra`

**FrontendEvent 事件类型**

- `js_error`, `resource_error`, `promise_error`, `api_error`
- `performance`, `page_view`, `page_leave`, `user_action`, `custom`

**AlertRule 指标类型**

- `frontend_error_count`, `backend_error_count`
- `api_avg_duration`, `api_error_rate`, `slow_sql_count`
- `comparator`: `gt/gte/lt/lte`
- `window_minutes`, `threshold`, `cooldown_minutes`
- `path_pattern`, `channels` (JSON 数组，预留推送渠道)
- `is_enabled`, `last_triggered_at`

### 1.2 App 目录结构

```text
backend/apps/monitoring/
├── __init__.py
├── apps.py
├── models.py
├── serializers.py
├── views.py
├── urls.py              # 公开上报 /api/monitoring/
├── admin_urls.py        # 管理查询 /api/admin/monitoring/
├── admin.py
├── middleware.py        # 请求拦截、耗时、异常、trace_id
├── sql.py               # 慢 SQL 上下文管理器
├── throttles.py         # 上报限流
├── services/
│   ├── storage.py       # 异步入库，容错
│   ├── sanitizer.py     # 敏感字段脱敏
│   ├── alerts.py        # 规则评估 + send_alert 扩展点
│   └── retention.py     # 过期数据清理
├── management/commands/
│   ├── cleanup_monitoring_data.py
│   └── evaluate_monitoring_alerts.py
├── migrations/
└── tests/
    └── test_monitoring_core.py
```

**分层职责**

| 层 | 职责 | 禁止 |
|----|------|------|
| middleware/sql | 采集上下文、计时、trace_id | 直接写复杂业务逻辑 |
| serializers | 字段校验、批量事件格式 | 业务判断 |
| views | 编排、分页、过滤 | 脱敏/存储细节 |
| services/storage | 入库、指纹、采样 | HTTP 响应 |
| services/alerts | 阈值判断、冷却、推送 stub | 修改业务数据 |

### 1.3 全局中间件

`MonitoringRequestMiddleware` 流程：

1. 检查 `MONITORING_ENABLED` 与 `MONITORING_SKIP_PATHS`
2. 生成/透传 `trace_id` → `request.monitoring_trace_id`，响应头 `X-Trace-Id`
3. 解析并脱敏 `request_payload`（GET query / JSON body）
4. `capture_sql(request)` 上下文内执行 `get_response`
5. 捕获未处理异常 → `store_backend_exception`
6. 正常响应 → 计算 `duration_ms` → `store_api_performance`
7. 可选 `MONITORING_CAPTURE_RESPONSE` 记录 JSON 响应（默认 false）

跳过路径默认包含：`/api/health/`、`/api/monitoring/`、静态资源、admin 静态。

### 1.4 慢 SQL 捕获

`sql.py` 使用 Django `connection.execute_wrapper`：

- 阈值：`MONITORING_SLOW_SQL_MS`（默认 500ms）
- 记录：sql 文本、sql_hash、duration_ms、path、method、trace_id、调用栈摘要
- 写入 `SqlPerformanceLog`；middleware 汇总 `slow_sql_count` 到 API 性能日志

### 1.5 上报接收接口

**POST `/api/monitoring/events/`**

- 权限：`AllowAny`（前端匿名上报）
- 限流：`MonitoringAnonThrottle` + `MonitoringUserThrottle`
- 支持单条或批量 `{ "events": [...] }`
- 校验 → 脱敏 → `store_frontend_events`
- 错误类事件同步写入 `MonitoringException`（source=frontend）

### 1.6 告警逻辑

`evaluate_alert_rules()`：

1. 遍历 `is_enabled=True` 的规则
2. 检查 `cooldown_minutes` 冷却
3. 按 `window_minutes` 窗口聚合 metric
4. `compare_value(value, comparator, threshold)`
5. 触发 → 创建 `AlertEvent` → 调用 `send_alert(event)`（第一版仅 logger，预留渠道）

**推送扩展点**

```python
def send_alert(event: AlertEvent) -> None:
    channels = event.rule.channels or []
    # 预留: wecom / email / sms
    for channel in channels:
        dispatch_alert(channel, event)
```

### 1.7 权限、防刷、限流

| 机制 | 实现 |
|------|------|
| 上报限流 | DRF throttle：`monitoring_anon` 300/min，`monitoring_user` 600/min |
| 批量上限 | `MONITORING_MAX_BATCH_SIZE=50` |
| Payload 上限 | `MONITORING_MAX_PAYLOAD_SIZE=16KB` |
| 服务端采样 | `MONITORING_SAMPLE_RATE` 随机丢弃 |
| 管理接口 | `IsAuthenticated` + `IsAdminUser` |
| 存储容错 | storage 层 try/except，失败只记 monitoring logger |
| 路径跳过 | 避免监控接口递归上报 |

### 1.8 后端 settings 环境变量

```python
MONITORING_ENABLED = true
MONITORING_SAMPLE_RATE = 1
MONITORING_SLOW_API_MS = 1000
MONITORING_SLOW_SQL_MS = 500
MONITORING_RETENTION_DAYS = 30
MONITORING_MAX_BATCH_SIZE = 50
MONITORING_MAX_PAYLOAD_SIZE = 16384
MONITORING_CAPTURE_RESPONSE = false
MONITORING_SKIP_PATHS = ("/api/health/", "/api/monitoring/", ...)
MONITORING_ANON_RATE = 300/min
MONITORING_USER_RATE = 600/min
MONITORING_LOG_LEVEL = INFO
```

### 1.9 管理 API 文档

前缀：`/api/admin/monitoring/`，需管理员登录。

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|----------|
| GET | `/overview/` | 总览大盘 | `days=1\|7\|30` |
| GET | `/frontend-events/` | 前端事件列表 | `days`, `keyword`, `level`, `event_type`, `page`, `page_size` |
| GET | `/exceptions/` | 异常列表 | `days`, `keyword`, `level`, `source=frontend\|backend` |
| GET | `/api-performance/` | 接口性能 | `days`, `path`, `min_duration`, `keyword` |
| GET | `/slow-sql/` | 慢 SQL | `days`, `path`, `min_duration`, `keyword` |
| GET/POST/PATCH | `/alert-rules/` | 告警规则 CRUD | — |
| GET | `/alert-events/` | 告警事件 | `days`, `status` |
| GET | `/health/` | 健康快照 + 触发评估 | — |

**overview 响应 data 结构**

```json
{
  "summary": {
    "frontend_errors": 0,
    "backend_errors": 0,
    "api_avg_duration_ms": 0,
    "slow_sql_count": 0,
    "open_alerts": 0
  },
  "trend": [{ "date": "06-15", "count": 12 }],
  "top_apis": [{ "path": "/api/v1/...", "avg_duration_ms": 800, "count": 100 }],
  "error_distribution": [{ "name": "js_error", "value": 5 }]
}
```

**上报响应**

```json
{ "code": 0, "message": "success", "data": { "received": 10, "stored": 8 } }
```

---

## 模块 2：前端监控 SDK（React）

### 2.1 目录结构

```text
frontend/src/utils/monitor/
├── index.js           # 公开 API：initMonitor, trackEvent, trackError, trackPageView
├── config.js          # 默认配置 + 环境变量
├── client.js          # 队列、批量上报、离线缓存
├── storage.js         # localStorage 离线队列
├── sanitize.js        # 脱敏 + payload 大小限制
└── collectors/
    ├── error.js       # window.onerror, unhandledrejection, resource error
    ├── performance.js # FP/FCP/LCP/CLS (PerformanceObserver)
    ├── request.js     # installAxiosMonitor
    └── router.js      # MonitorRouteTracker 组件
```

### 2.2 自动采集

| 类型 | 触发 | event type |
|------|------|------------|
| JS 运行错误 | `window.onerror` | `js_error` |
| Promise 未捕获 | `unhandledrejection` | `promise_error` |
| 资源加载失败 | capture phase error | `resource_error` |
| 接口异常 | Axios response error interceptor | `api_error` |
| 接口耗时 | Axios 成功/失败均记录 duration | `custom` / name=`api_request` |
| Web Vitals | PerformanceObserver | `performance` |
| 路由 PV | Router 组件 / MonitorRouteTracker | `page_view` |
| 页面停留 | visibilitychange / route leave | `page_leave` |

### 2.3 公开 API

```js
// 初始化（main.jsx 一次）
initMonitor(options?)

// 手动埋点
trackEvent(name, payload?, { type, level, message, route }?)
trackError(error, context?)
trackPageView(route, meta?)

// 辅助
setMonitorUser(user)          // 绑定 user_id
flushMonitorQueue({ beacon }) // 立即上报
configureMonitor(overrides)   // 运行时改配置
installAxiosMonitor(instance) // 在 http.js 内调用
```

### 2.4 上报策略

- **批量**：默认 `batchSize=10`，满批立即 flush
- **定时**：`flushInterval=10000ms`
- **离线**：失败写入 localStorage，online 后补发
- **页面关闭**：`beforeunload` / `visibilitychange=hidden` 用 `sendBeacon`
- **队列上限**：`maxQueueSize=200`，超出截断保留最新
- **采样**：`sampleRate` 0~1 随机丢弃
- **忽略**：`ignoreErrors` 白名单、`ignoreUrls` 跳过监控接口自身

### 2.5 配置项（环境变量）

| 变量 | 默认 | 说明 |
|------|------|------|
| `VITE_MONITORING_ENABLED` | prod=true, dev=false | 总开关 |
| `VITE_MONITORING_SAMPLE_RATE` | 1 | 前端采样率 |
| `VITE_MONITORING_BATCH_SIZE` | 10 | 批量大小 |
| `VITE_MONITORING_FLUSH_INTERVAL` | 10000 | flush 间隔 ms |
| `VITE_MONITORING_MAX_QUEUE_SIZE` | 200 | 队列上限 |
| `VITE_MONITORING_MAX_PAYLOAD_SIZE` | 16384 | 单条 payload 上限 |
| `VITE_APP_VERSION` | — | release 版本 |

### 2.6 http.js 接入（低侵入）

在 `getAxios()` 创建 instance 后：

```js
import { installAxiosMonitor } from '@/utils/monitor'
installAxiosMonitor(instance)
```

业务代码零改动，自动采集所有经统一 client 的请求。

---

## 模块 3：监控管理后台（React Admin）

### 3.1 页面规划

单页 Tab 或多路由，推荐 Tab 聚合（参考 `MonitoringDashboardPage.jsx`）：

| Tab | 功能 |
|-----|------|
| 总览大盘 | 指标卡片 + 异常趋势折线 + Top API 条形图 + 错误分布饼图 |
| 前端异常 | 列表 + keyword/level/days 筛选 + 详情弹窗 |
| 后端异常 | 同上，source=backend |
| 接口性能 | path/min_duration 筛选 + 耗时排行 |
| 慢 SQL | sql_hash/path 检索 + SQL 详情 |
| 埋点事件 | event_type 筛选 + 自定义事件统计 |
| 告警配置 | 规则 CRUD + 告警事件列表 |

### 3.2 UI 实现要点

- 布局：`AdminShell` + `AdminTabBar` + `AdminTable` + `AdminPagination`
- 图表：复用 `@/components/charts/EChart`，option 在页面内 `build*Option()` 或抽到 `charts/options/monitoring.js`
- 筛选：`FilterBar` 组件统一 days/keyword/level
- 详情：Modal 展示 stack、request_data、payload（JSON 格式化）
- 空态/加载：`AdminLoading`、`EmptyState`

### 3.3 权限

- 路由 meta：`requiresAuth: true`, `permissions: ['admin']` 或等价守卫
- API 层：`adminMonitoring` service 走已有 token 注入
- 后端：`IsAdminUser` 硬校验，前端仅做体验层隐藏

### 3.4 API Service 封装

```text
frontend/src/services/api/adminMonitoring.js
```

```js
export const adminMonitoring = {
  getOverview: (params) => request('GET', '/api/admin/monitoring/overview/', { params }),
  getFrontendEvents: (params) => request('GET', '/api/admin/monitoring/frontend-events/', { params }),
  getExceptions: (params) => request('GET', '/api/admin/monitoring/exceptions/', { params }),
  getApiPerformance: (params) => request('GET', '/api/admin/monitoring/api-performance/', { params }),
  getSlowSql: (params) => request('GET', '/api/admin/monitoring/slow-sql/', { params }),
  getAlertRules: (params) => request('GET', '/api/admin/monitoring/alert-rules/', { params }),
  createAlertRule: (data) => request('POST', '/api/admin/monitoring/alert-rules/', { data }),
  patchAlertRule: (id, data) => request('PATCH', `/api/admin/monitoring/alert-rules/${id}/`, { data }),
  getAlertEvents: (params) => request('GET', '/api/admin/monitoring/alert-events/', { params }),
  getHealth: () => request('GET', '/api/admin/monitoring/health/'),
}
```

---

## 模块 4：接入与部署

### 4.1 前端全局初始化

```js
// main.jsx — 在 render 前
import { initMonitor, setMonitorUser } from '@/utils/monitor'
initMonitor()

// authStore 订阅或登录成功后
setMonitorUser({ id: user.id })
```

路由埋点（React Router）：

```jsx
import { MonitorRouteTracker } from '@/utils/monitor'
<BrowserRouter>
  <MonitorRouteTracker />
  ...
</BrowserRouter>
```

### 4.2 后端注册

**settings/base.py**

```python
INSTALLED_APPS += ["apps.monitoring"]
MIDDLEWARE += ["apps.monitoring.middleware.MonitoringRequestMiddleware"]
```

**config/urls.py**

```python
path("api/monitoring/", include("apps.monitoring.urls")),
```

**apps/console/urls.py**

```python
path("monitoring/", include("apps.monitoring.admin_urls")),
```

### 4.3 Docker 环境变量

docker-compose 示例：

```yaml
services:
  backend:
    environment:
      MONITORING_ENABLED: "true"
      MONITORING_SAMPLE_RATE: "0.1"
      MONITORING_RETENTION_DAYS: "30"
      MONITORING_SLOW_SQL_MS: "500"
      MONITORING_ANON_RATE: "300/min"
  frontend:
    environment:
      VITE_MONITORING_ENABLED: "true"
      VITE_MONITORING_SAMPLE_RATE: "0.1"
```

### 4.4 分阶段上线

| 阶段 | 环境 | 配置 | 验证 |
|------|------|------|------|
| 1 | dev | `VITE_MONITORING_ENABLED=false` | SDK debug 控制台 |
| 2 | test | sample=1 | 字段、脱敏、列表、告警 |
| 3 | prod 首日 | sample=0.05 | DB 写入量、慢查询 |
| 4 | prod 稳定 | sample 逐步提到 0.2~1 | 调整 retention |

**数据回溯**：历史无监控数据；上线后从 `created_at` 起算，不做回填。

### 4.5 定时任务

```bash
# 每日低峰清理 30 天前数据
python manage.py cleanup_monitoring_data --days 30

# 每 1-5 分钟评估告警
python manage.py evaluate_monitoring_alerts
```

Celery beat / cron / K8s CronJob 均可；清理与评估分离调度。

---

## 模块 5：编码约束与扩展点

### 5.1 解耦原则

- 业务 View/Service **禁止**直接写监控表；仅通过 middleware + SDK 自动采集，或显式调用 `trackEvent`。
- 监控 app **禁止** import 业务 app 的 models（避免循环依赖）；user_id 仅存 UUID。
- 前端 SDK **禁止**修改 Axios 业务拦截逻辑顺序；`installAxiosMonitor` 独立注册。
- 监控异常 **禁止**改变 HTTP 状态码或业务响应体。

### 5.2 预留扩展点

| 扩展点 | 位置 | 用途 |
|--------|------|------|
| `send_alert(event)` | `services/alerts.py` | 企业微信/邮件/短信 |
| `AlertRule.channels` | JSON 字段 | 渠道配置 |
| `beforeSend(event)` | SDK config | 业务侧过滤/ enrich |
| `ServiceHealthSnapshot` | models | 自定义健康探针 |
| `AlertRule.MetricType` | 枚举扩展 | 自定义维度统计 |
| 日志检索 | 未来 app | 对接现有 logging 配置 |

### 5.3 完整落地顺序

```
1. 建库：models.py + makemigrations + migrate
2. 后端 services：sanitizer → storage → retention → alerts
3. 后端采集：middleware + sql.py
4. 后端接口：urls + views + serializers + throttles
5. 后端测试：test_monitoring_core.py
6. 前端 SDK：config → client → collectors → index.js
7. 前端挂载：http.js installAxiosMonitor + main.jsx initMonitor
8. 后台 API：adminMonitoring.js
9. 后台页面：MonitoringDashboardPage + 路由注册
10. 运维：management commands + Docker env + monitoring.md
11. 灰度：dev 关 → test 全开 → prod 低采样
12. 业务埋点：按需 trackEvent，非必须
```

### 5.4 测试要点

- 上报单条/批量、超限 batch、超大 payload 截断
- 脱敏字段不出现在 DB
- middleware 异常不影响 500 响应格式
- throttle 429 不拖垮业务
- 告警冷却不重复触发
- cleanup 命令按 retention 删除
- SDK 离线缓存补发

---

## 与本项目已有实现的对照

本项目（ScriptForge）已落地上述架构，可直接作为参考实现：

| 能力 | 路径 |
|------|------|
| 后端 models | `backend/apps/monitoring/models.py` |
| 中间件 | `backend/apps/monitoring/middleware.py` |
| 慢 SQL | `backend/apps/monitoring/sql.py` |
| 告警 | `backend/apps/monitoring/services/alerts.py` |
| 前端 SDK | `frontend/src/utils/monitor/` |
| 后台页 | `frontend/src/pages/Admin/monitoring/MonitoringDashboardPage.jsx` |
| 文档 | `backend/docs/monitoring.md` |

扩展需求时优先改上述文件，保持目录与 API 契约稳定。
