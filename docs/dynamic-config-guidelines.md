# 动态配置中心开发规范

## 适合进入配置中心

- 运营文案、页面展示数据、业务阈值、功能开关。
- 创作流程默认值、低风险限额、监控采样率。
- 前端需要在不重新打包的情况下调整的展示规则。

## 不允许进入配置中心

- 密钥、数据库、Redis、对象存储、第三方凭证。
- `DEBUG`、`ALLOWED_HOSTS`、CORS、安全响应头。
- JWT、Django app、用户模型、数据库 schema 枚举。
- 已有专表管理的金额、套餐、Agent 规则、告警规则。

## 新增配置流程

1. 在 `backend/apps/system_config/defaults.py` 增加默认配置、类型和 `validation_schema`。
2. 执行 `python manage.py seed_system_config` 初始化到数据库。
3. 后端通过 `get_config/get_int/get_bool/get_json` 读取。
4. 前端通过 `useConfig/getConfigValue` 读取。
5. 如配置会影响安全、支付或生产稳定性，设置 `is_sensitive`、`requires_restart` 或限制为非公开。
6. 为业务接入点保留短期 fallback，并在迁移稳定后清理。
7. Code review 时检查是否存在新硬编码业务阈值、文案和开关。

## 缓存与发布

- 写入配置后后台会主动失效缓存。
- 前端保存后应刷新公开配置 store。
- Redis 不可用时服务层会退化为直接读库或本地缓存，不应阻断主流程。
- 高风险配置必须填写变更原因，后续可接入审批或二次确认。
