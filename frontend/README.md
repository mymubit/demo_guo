# ScriptForge Workbench (PC)

React 18 + Vite + TypeScript strict 短剧创作工作台前端。

## Scripts

```bash
npm install
npm run dev
npm run test
npm run lint
npm run typecheck
npm run build
```

## API

- Base: `VITE_API_BASE_URL`（默认空字符串，走同源 `/api`；生产由 nginx 反代）
- Drama contract: `/api/v1/drama/*`（见 `workbench/api-contract.yaml`）
- Workbench form: `GET /api/v1/drama/meta/workbench-form/`（运行时阶段/模块/参数字段定义，按 `skills_bundle_version` 缓存）
- Auth: `/api/auth/login|refresh|logout/`

## Architecture

- `src/services` — Axios 请求层、Token 注入/刷新、错误码映射、SSE Job 客户端
- `src/hooks/useWorkbenchDefinition` — 运行时加载 `/api/v1/drama/meta/workbench-form/`，按 skills bundle version 缓存
- `src/config/workbench.ts` — 仅保留 PC 宽度与 UI widget 映射（无业务枚举/默认）
- `src/pages` — 登录 / 项目 / 设置 / 三栏工作台 / 外部评测 / 配置后台
- `src/components/workbench` — PipelineRail · StageCanvas · ModulePanel · QualityLoopPanel
