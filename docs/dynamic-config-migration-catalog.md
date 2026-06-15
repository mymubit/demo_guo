# 动态配置迁移清单

## 已初始化配置

| 配置键 | 分类 | 类型 | 默认值 | 公开 | 接入状态 |
| --- | --- | --- | --- | --- | --- |
| `system.site_name` | system | string | `ScriptForge 短剧创作平台` | 是 | 后台系统快照 |
| `system.support_email` | system | string | `support@scriptforge.local` | 是 | 后台系统快照 |
| `payment.default_method` | payment | string | `mock` | 是 | 前端充值订单默认支付方式 |
| `creation.default_episode_count` | creation | int | `80` | 是 | 创作表单默认集数 |
| `creation.max_outline_chars` | creation | int | `8000` | 是 | 创作表单大纲字数上限 |
| `creation.ai_field_fallback_cost` | creation | int | `10` | 是 | AI 字段扣费展示兜底 |
| `monitoring.frontend_sample_rate` | monitoring | float | `1.0` | 是 | 待接入 |
| `security.rate_limit_per_minute` | security | int | `120` | 否 | 待评估后接入 |
| `home.hero_stats` | copywriting | array | `[]` | 是 | 待接入 |

## 分批迁移策略

P0 优先迁移：

- 创作表单默认值、字数上限、题材/格式/平台展示文案。
- 首页营销数据与运营文案。
- 支付默认方式、币种展示兜底。

P1 灰度迁移：

- 状态展示文案、功能开关。
- 监控采样率和低风险保留天数。
- 创作流程可热更新阈值。

P2 保留代码或环境变量：

- 路由、导航、设计 token、图标映射。
- 错误码、API 协议枚举。
- 监控客户端本地队列参数。

禁止迁移：

- `SECRET_KEY`、第三方 API Key、数据库连接、Redis 地址。
- `DEBUG`、`ALLOWED_HOSTS`、CORS、安全响应头。
- JWT、用户模型、Django app 配置。
- 数据库模型状态枚举和需要 migration 的 schema 级字段。

## 操作流程

1. 在 `backend/apps/system_config/defaults.py` 增加配置定义和校验规则。
2. 执行 `python manage.py seed_system_config` 导入默认值。
3. 后端通过 `apps.system_config.services.get_config()` 读取。
4. 前端通过 `useConfig()` 或 `getConfigValue()` 读取。
5. 后台在 `/admin/system/configs` 在线修改，并通过“刷新缓存”立即生效。
6. 稳定后移除对应静态硬编码 fallback。
