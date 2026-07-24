# ScriptForge V3 Frontend

React + TypeScript 创作者工作台。产品 API 为 `/api/v3/`；认证仍为 `/api/v1/auth/`。旧 `/api/v2` 与 `src/studio/**` 已下线（410 / 已删）。

## 主要路由

- `/dashboard`：创作仪表盘
- `/projects/:id`：项目概览
- `/projects/:id/topic|blueprint|episodes|editor|quality|delivery`：主链工作区
- `/models`：模型供应商与角色映射
- `/logs`：命令运行与 LLM 调用日志
- `/system`：系统配置（平台 / 评分预设）
- `/billing`：套餐展示壳（无支付）

业务代码在 `src/pages/`、`src/services/v3/`、`src/app/`。

## 开发

```bash
npm run dev
npm run typecheck
npm test
npm run build
```
