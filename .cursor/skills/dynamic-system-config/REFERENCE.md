# 动态配置中心落地方案模板

## 一、后端 Django 设计

### 1. 数据库表结构

推荐新增独立 `system_config` APP，至少包含配置分类表和配置项表。

`ConfigCategory`：

- `id`：主键。
- `code`：分类编码，唯一，例如 `system`、`business`、`payment`、`membership`、`creation`。
- `name`：分类名称。
- `description`：分类说明。
- `is_enabled`：是否启用。
- `sort_order`：排序值。
- `created_at` / `updated_at`：审计时间。

`SystemConfig`：

- `id`：主键。
- `category`：外键，关联 `ConfigCategory`，允许按分类聚合。
- `key`：配置键，全局唯一，建议使用点分命名，例如 `creation.max_script_count`。
- `name`：配置名称，用于后台展示。
- `value_type`：配置值类型，使用 `models.TextChoices`，可选 `string`、`number`、`boolean`、`json`、`array`。
- `value`：配置值，建议使用 `JSONField`，按 `value_type` 做校验与转换。
- `default_value`：默认值，使用 `JSONField`，作为统一兜底来源。
- `description`：备注说明。
- `is_enabled`：是否启用。
- `is_sensitive`：是否敏感配置，敏感配置禁止下发前端。
- `created_at` / `updated_at`：审计时间。

索引与约束：

- `key` 设置唯一约束，防止重复配置键。
- `category + is_enabled` 建普通索引，支持后台筛选。
- `is_enabled + key` 建索引，支持读取有效配置。
- 可选：`category + key` 唯一约束，但如果 `key` 已全局唯一通常不再需要。

类型适配：

- 存储层统一 `JSONField`，避免字符串反序列化散落在业务代码。
- Serializer 或 service 层根据 `value_type` 校验 `value`。
- 读取入口统一返回 Python 原生类型。

### 2. APP 分层结构

```text
backend/apps/system_config/
├── __init__.py
├── admin.py
├── apps.py
├── models.py
├── serializers.py
├── views.py
├── urls.py
├── services.py
├── permissions.py
├── cache.py
├── validators.py
├── tasks.py
├── management/
│   └── commands/
│       └── import_system_configs.py
└── migrations/
```

职责建议：

- `models.py`：只定义数据结构、枚举、索引与约束。
- `serializers.py`：只做序列化、参数校验、类型校验。
- `services.py`：封装配置读取、写入、批量获取、缓存刷新、默认值策略。
- `cache.py`：封装 Redis 和内存缓存兜底。
- `views.py`：DRF ViewSet 与 action，不承载业务逻辑。
- `permissions.py`：管理员可写、普通用户只读。
- `tasks.py`：定时预热或同步缓存。

### 3. RESTful 接口全集

基础路由建议：`/api/v1/system-config/`

- `GET /categories/`：分类列表。
- `POST /categories/`：新增分类，管理员。
- `PATCH /categories/{id}/`：编辑分类，管理员。
- `GET /configs/`：分页查询配置，支持 `category`、`keyword`、`is_enabled`、`value_type`。
- `GET /configs/{id}/`：配置详情。
- `POST /configs/`：新增配置，管理员。
- `PUT/PATCH /configs/{id}/`：编辑配置，管理员。
- `POST /configs/{id}/enable/`：启用配置，管理员。
- `POST /configs/{id}/disable/`：禁用配置，管理员。
- `DELETE /configs/{id}/`：删除配置，管理员；高风险场景优先软删除。
- `POST /configs/batch/`：按 key 列表批量获取配置。
- `GET /configs/value/?key=xxx`：根据配置键单点取值。

响应格式遵循项目统一格式：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

### 4. 缓存方案

读取链路：

1. `get_config(key, default_val=None)` 先读缓存。
2. 缓存命中直接返回。
3. 缓存未命中查数据库中 `is_enabled=True` 的配置。
4. 查到后按 `value_type` 转换并写入缓存。
5. 查不到时返回数据库默认值或调用方传入默认值。

写入链路：

1. 配置新增、编辑、启用、禁用、删除必须走 service。
2. service 完成数据库事务后刷新单 key 缓存。
3. 批量导入或批量修改后刷新分类缓存或全量缓存。

缓存策略：

- Redis key：`system_config:{key}`，批量缓存可使用 `system_config:all`。
- Redis TTL：业务配置可设置 5 至 30 分钟；关键配置可永久缓存并通过写入主动失效。
- 无 Redis 时使用模块级内存缓存，带 TTL 与最大容量保护。
- 定时任务定期预热高频配置，作为写入刷新失败的兜底。

注意：

- 敏感配置不得进入前端批量接口。
- 日志记录配置 key、操作人、结果，不记录敏感 value。
- 多表写入和批量导入使用 `transaction.atomic`。

### 5. 全局工具封装

推荐服务入口：

```python
def get_config(key: str, default_val=None):
    return SystemConfigService.get_value(key=key, default_val=default_val)
```

批量入口：

```python
def get_configs(keys: list[str]) -> dict[str, object]:
    return SystemConfigService.get_values(keys=keys)
```

接入规则：

- 业务代码只能依赖 `services.py` 暴露的读取函数。
- 不允许在视图、任务、模型方法中直接查询 `SystemConfig.objects.get(...)`。
- 默认值统一来自配置表 `default_value` 或服务层注册表，避免前端和业务逻辑各自兜底。

### 6. 权限控制

- 列表、详情、批量读取：登录用户可读，敏感配置需管理员或直接过滤。
- 新增、编辑、启用、禁用、删除：仅管理员。
- 如果项目已有角色权限体系，复用现有权限类。
- 删除操作建议软删除或二次确认，并记录审计日志。

### 7. 数据迁移脚本模板

管理命令输入建议使用 JSON 文件：

```json
[
  {
    "category": "creation",
    "key": "creation.max_script_count",
    "name": "最大脚本数量",
    "value_type": "number",
    "value": 10,
    "default_value": 10,
    "description": "创作业务单项目最大脚本数量",
    "is_enabled": true
  }
]
```

导入策略：

- 使用 `update_or_create` 保证可重复执行。
- 使用 `transaction.atomic` 包裹批量导入。
- 导入后刷新缓存。
- 对敏感配置要求手工确认，不从前端常量自动导入。

## 二、前端改造设计

### 1. API 封装

在 `src/api` 或项目现有请求层新增配置模块：

- `getConfigList(params)`：配置分页。
- `getConfigDetail(id)`：配置详情。
- `createConfig(payload)`：新增。
- `updateConfig(id, payload)`：编辑。
- `enableConfig(id)` / `disableConfig(id)`：启停。
- `deleteConfig(id)`：删除。
- `batchGetConfigs(keys)`：批量读取。
- `getConfigValue(key)`：单点读取。

必须复用全局请求实例、Token 注入、错误码映射和消息提示策略。

### 2. 全局初始化

- 应用启动时按页面需要批量拉取配置。
- 将配置放入现有全局状态方案，或新增轻量 `ConfigProvider`。
- 高频公共配置使用一次批量请求，页面私有配置按页面懒加载。
- 避免每个组件单独请求同一配置。

### 3. Hook 与工具函数

`useConfig(key, defaultValue)` 行为：

- 优先从全局配置状态读取。
- 未命中时返回统一默认值，不在组件内散落硬编码。
- 可选支持 `refreshConfig(key)` 手动刷新。
- 对敏感配置不提供前端读取能力。

组件用法示例：

```jsx
const maxScriptCount = useConfig('creation.max_script_count', 10)
```

### 4. 后台管理页面

页面建议：

- 配置分类总览页：展示分类、数量、启用状态。
- 配置列表页：分页、分类筛选、关键词搜索、状态筛选、类型筛选。
- 新增/编辑弹窗：根据 `value_type` 自动渲染编辑控件。
- 状态快捷切换：启用、禁用。
- 批量操作：批量启用、禁用、导出；删除谨慎开放。

值编辑控件：

- `string`：文本输入或多行输入。
- `number`：数字输入，支持最小值、最大值扩展。
- `boolean`：开关。
- `json`：JSON 文本框，提交前校验。
- `array`：JSON 数组编辑，提交前校验为数组。

UI 规范：

- 复用现有后台布局、表格、弹窗、按钮、表单组件。
- 使用 TailwindCSS，并用 `clsx`、`tailwind-merge` 处理条件类名。
- 管理入口仅管理员可见；路由层和页面层都要做权限限制。
- 操作成功用 `sonner` 提示，失败走全局错误处理。

### 5. 存量代码改造示例

旧代码：

```jsx
const MAX_SCRIPT_COUNT = 10

if (scripts.length >= MAX_SCRIPT_COUNT) {
  toast.error('最多只能创建 10 个脚本')
}
```

新代码：

```jsx
const maxScriptCount = useConfig('creation.max_script_count', 10)

if (scripts.length >= maxScriptCount) {
  toast.error(`最多只能创建 ${maxScriptCount} 个脚本`)
}
```

后端旧代码：

```python
MAX_RETRY_COUNT = 3
```

后端新代码：

```python
from apps.system_config.services import get_config

max_retry_count = get_config("system.max_retry_count", 3)
```

## 三、分步迁移落地步骤

1. 梳理硬编码来源：前端常量文件、后端常量文件、枚举、文案、阈值、开关。
2. 建立 `system_config` APP、模型、迁移、接口、缓存和权限。
3. 编写导入模板，将现有硬编码配置初始化入库。
4. 开发前端 API、全局配置状态、`useConfig` 和后台管理页面。
5. 灰度替换：从低风险配置开始，将写死常量改为动态读取。
6. 验证后台修改后缓存刷新和业务实时生效。
7. 完成回归测试后，逐步清理已废弃静态常量文件。

## 四、约束与规范

- 保留原常量文件作为短期回退来源，确认全部迁移后再清理。
- 迁移期间同一配置只能有一个权威来源，避免数据库和代码值长期分叉。
- 敏感配置必须标记 `is_sensitive=True`，默认不暴露给前端。
- 配置修改日志建议预留 `SystemConfigChangeLog`：记录配置 key、旧值、新值、操作人、原因、时间、请求来源。
- 新增配置必须先登记 key、类型、默认值、使用范围和负责人，再接入业务代码。
- 单元测试覆盖类型校验、缓存命中、缓存失效、批量读取、权限控制和默认值兜底。
