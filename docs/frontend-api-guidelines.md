# 前端接口与数据处理规范

## 请求入口

- 页面、组件、hook 禁止直接调用 `axios` 或 `fetch`，统一通过 `src/services/api.js` 暴露的业务模块访问后端。
- `src/services/http.js` 只负责请求发送、Token 注入、响应解包、错误归一化和刷新重试。
- 下载、健康检查、SimpleJWT refresh/verify 等非标准响应接口必须显式使用 `rawResponse` 或 `responseType: 'blob'`。

## 响应处理

- 常规接口默认按 `{ code, message, data }` 解析。
- 分页接口统一在 service 层转换为 `{ items, pagination }`，其中 `pagination` 固定包含 `total/page/page_size/total_pages`。
- 页面不得直接依赖后端 `data + pagination` 的原始嵌套结构。
- 禁止新增 `{ items }`、裸数组分页、`pagination || res` 等旧结构兼容分支。
- 业务错误不得静默吞掉，必须进入页面错误态或消息提示。

## 字段与枚举

- 后端字段以新版契约为准；业务主键统一使用 `project_id`，不得再兼容 `task_id/taskId/id`。
- 页面不得直接做旧字段兜底映射；必要的展示字段转换只能在 service 内部 adapter 单点完成。
- 枚举值统一维护在 `src/services/constants/businessEnums.js`。
- 错误码统一维护在 `src/services/constants/errorCodes.js`。
- 新增页面禁止硬编码业务状态、支付方式、错误码和权限字段。

## 鉴权与权限

- access token 通过 `Authorization: Bearer <token>` 注入。
- `401/4011` 优先尝试 refresh，刷新失败后清理登录态并跳转登录页。
- 管理员权限统一使用新版后端字段 `is_staff/is_superuser`，业务页面不要自行发散实现。

## 前后端同步

- 后端新增或修改接口时，需同步说明 URL、method、入参、响应、分页、错误码、权限和枚举。
- 前端适配时先更新 service/adapter，再改页面消费逻辑。
- 高风险接口必须在 `docs/frontend-backend-contract-audit.md` 登记并完成联调状态更新。
