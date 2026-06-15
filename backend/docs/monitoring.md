# 自研业务监控体系

## 接入范围

- 前端：JS 错误、资源加载错误、Promise 未捕获异常、接口异常、Web Vitals、路由 PV、页面停留、自定义埋点。
- 后端：全局异常、接口耗时、请求上下文、慢 SQL、服务健康快照、告警规则与告警事件。
- 数据：统一写入 Django 默认数据库，监控失败不影响业务请求。

## 公开上报接口

### `POST /api/monitoring/events/`

支持单条或批量：

```json
{
  "events": [
    {
      "type": "js_error",
      "level": "error",
      "name": "TypeError",
      "message": "Cannot read properties of undefined",
      "page_url": "https://example.com/admin/monitoring",
      "route": "/admin/monitoring",
      "session_id": "uuid",
      "trace_id": "trace-id",
      "payload": {
        "stack": "..."
      },
      "performance": {
        "fcp": 1200,
        "lcp": 2400,
        "cls": 0.02
      },
      "timestamp": "2026-06-15T05:00:00Z"
    }
  ]
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "received": 1,
    "stored": 1
  }
}
```

限制：

- 单批默认最多 50 条，`MONITORING_MAX_BATCH_SIZE` 可配置。
- 单条 `payload` / `performance` 默认 16KB，`MONITORING_MAX_PAYLOAD_SIZE` 可配置。
- 上报接口允许匿名访问，但使用 `monitoring_anon` / `monitoring_user` throttle。
- 服务端会脱敏 password、token、authorization、cookie、secret、api_key、手机号、邮箱等字段。

## 后台管理接口

所有后台接口挂载在 `/api/admin/monitoring/`，要求登录且管理员权限。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/overview/` | 监控总览、趋势图、接口耗时排行、错误分布 |
| GET | `/frontend-events/` | 前端事件列表，支持 `days`、`keyword`、`level`、`event_type` |
| GET | `/exceptions/` | 异常列表，支持 `source=frontend/backend` |
| GET | `/api-performance/` | 接口性能列表，支持 `path`、`min_duration` |
| GET | `/slow-sql/` | 慢 SQL 列表，支持 `path`、`min_duration` |
| GET/POST/PATCH | `/alert-rules/` | 告警规则查询、新增、更新 |
| GET | `/alert-events/` | 告警事件列表 |
| GET | `/health/` | 服务健康快照并触发一次告警评估 |

分页响应沿用项目标准：

```json
{
  "code": 0,
  "message": "success",
  "data": [],
  "pagination": {
    "total": 0,
    "page": 1,
    "page_size": 10,
    "total_pages": 1
  }
}
```

## 前端初始化

`src/main.jsx` 全局调用：

```js
import { initMonitor } from '@/utils/monitor'

initMonitor()
```

手动埋点：

```js
import { trackEvent, trackError, trackPageView } from '@/utils/monitor'

trackEvent('script_export_clicked', { project_id: projectId })
trackError(error, { name: 'script_export_failed' })
trackPageView('/creation')
```

## 后端启用

1. `INSTALLED_APPS` 注册 `apps.monitoring`。
2. `MIDDLEWARE` 注册 `apps.monitoring.middleware.MonitoringRequestMiddleware`。
3. `config/urls.py` 挂载 `/api/monitoring/`。
4. `apps.console.urls` 挂载 `/api/admin/monitoring/`。
5. 执行迁移：

```bash
python manage.py migrate monitoring
```

## 定时清理和告警

清理过期数据：

```bash
python manage.py cleanup_monitoring_data --days 30
```

评估告警规则：

```bash
python manage.py evaluate_monitoring_alerts
```

生产建议通过 cron、K8s CronJob 或现有 worker 调度：

- 清理：每天低峰执行一次。
- 告警评估：每 1-5 分钟执行一次。

## 灰度上线建议

1. 开发环境：`VITE_MONITORING_ENABLED=false`，仅控制台 debug。
2. 测试环境：`MONITORING_SAMPLE_RATE=1`，验证字段、脱敏、列表和告警。
3. 生产首日：`MONITORING_SAMPLE_RATE=0.05`，先观察 DB 写入量和慢查询。
4. 稳定后逐步放量，并根据表增长调整 `MONITORING_RETENTION_DAYS`。
