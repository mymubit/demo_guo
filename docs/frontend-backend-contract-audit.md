# 前端 v1.0 与新版后端接口差异清单

## 核心契约

- 后端主路由保持 `/api/` 与 `/api/admin/`，当前未使用 `/api/v1/`。
- 常规响应格式为 `{ code, message, data }`，成功码为 `0`。
- 分页列表额外返回 `pagination: { total, page, page_size, total_pages }`。
- 业务错误多数为 HTTP 200，需要按 `code` 判断；限流和签名失败可能返回非 200。
- Token 使用 `Authorization: Bearer <access>`，刷新接口 `/api/auth/refresh/` 返回 SimpleJWT 原生 `{ access }`。
- 后端字段以新版契约为准，前端不再保留旧字段、旧路由、旧分页结构兼容。

## 已识别差异

| 模块 | 前端旧契约 | 新版后端契约 | 适配位置 | 状态 |
| --- | --- | --- | --- | --- |
| auth | 仅登录/登出，未显式区分 refresh 原生响应 | `/api/auth/refresh/`、`verify/` 为 SimpleJWT 原生结构 | `src/services/http.js`、`src/services/auth.js` | 已适配 |
| auth | 只处理 `401` | 需同时处理 `401`、`4011`、`40101` | `src/services/constants/errorCodes.js`、`src/services/http.js` | 已适配 |
| admin auth | 权限判断兼容 `is_admin` | 新版仅按 `is_staff/is_superuser` 判断 | `src/store/authStore.js`、`src/router/guards.jsx` | 兼容已清理 |
| pagination | 兼容旧 `{items}`、裸数组分页和顶层分页展开 | 统一 `{data,pagination}`，service 输出 `{items,pagination}` | `src/services/adapters/listAdapter.js` | 兼容已清理 |
| creation catalog | 旧 `/api/workflow/catalog/`、`/api/workflow/nodes/` | `/api/creation/fusion/catalog/`、`/api/creation/fusion/nodes/`；旧路径返回 410 | `src/services/creation.js` | 旧路径已下线 |
| agent catalog | 旧 `/api/agent/catalog/` | `/api/creation/agents/catalog/`；旧路径返回 410 | `src/services/creation.js` | 旧路径已下线 |
| creation id | 页面混用 `task_id/taskId/project_id/id` | 业务只读 `project_id` | `src/services/adapters/businessAdapters.js` | 兼容已清理 |
| works status | 页面状态 `generating/draft` 直接映射分散 | 后端状态 `running/pending/awaiting/completed/failed` | `src/services/constants/businessEnums.js`、`src/services/works.js` | 已适配 |
| orders | 响应可能嵌套 `order` | 页面需要稳定订单对象 | `src/services/adapters/businessAdapters.js` | 已适配 |
| membership | 兼容旧到期字段 `expires_at` | 新版会员到期字段为 `end_at` | `src/services/adapters/businessAdapters.js` | 兼容已清理 |

## 后续联调模板

| 模块 | 页面/调用点 | URL | Method | 入参 | 响应类型 | 字段差异 | 错误码 | 权限 | 自测用例 | 联调状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| auth | 登录页 | `/api/auth/login/` | POST | `phone/password` | 统一 JSON | `data.user/access/refresh` | `4001/401` | AllowAny | 正常、密码错误、非法手机号 | 自动化覆盖（`apps/portal/tests/test_auth_api.py`） |
| auth | 自动刷新 | `/api/auth/refresh/` | POST | `refresh` | SimpleJWT raw | `access` 不在 `data` 内 | `401` | refresh token | access 过期后自动重试 | 自动化覆盖（`apps/portal/tests/test_auth_api.py`） |
| creation | 创作提交 | `/api/creation/submit/` | POST | 表单 payload | 统一 JSON | `project_id` | `4001/403` | 登录 | 正常、余额不足、非法参数 | 自动化覆盖（`apps/portal/tests/test_creation_submit_api.py`） |
| works | 作品列表 | `/api/works/` | GET | `page/page_size/status` | 分页 JSON | `data + pagination` | `401` | 登录 | 空列表、分页、状态筛选 | 自动化覆盖（`apps/portal/tests/test_works_api.py`） |
| admin | 用户列表 | `/api/admin/users/` | GET | `page/page_size` | 分页 JSON | `data + pagination` | `401/403` | 管理员 | 无权限、分页、搜索 | 自动化覆盖（`apps/console/tests/test_admin_users_api.py`） |

## 故意保留的 410 路由（AUD-013）

以下旧路径**故意保留**并返回 HTTP 410 + `deprecated.canonical_path`，供客户端迁移提示，**不应删除**：

| 旧路径 | 替代路径 | 定义文件 |
| --- | --- | --- |
| `GET /api/agent/catalog/` | `GET /api/creation/agents/catalog/` | `backend/apps/portal/agent/urls.py` |
| `GET /api/workflow/catalog/` | `GET /api/creation/fusion/catalog/` | `backend/apps/portal/workflow/urls.py` |
| `GET /api/workflow/nodes/` | `GET /api/creation/fusion/nodes/` | `backend/apps/portal/workflow/urls.py` |

前端已在 `src/services/creation.js` 使用 canonical 路径；旧路径仅作兼容探测与文档说明。
