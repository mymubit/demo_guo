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
- Auth: `/api/auth/login|refresh|logout/`

## Architecture

- `src/services` — Axios 请求层、Token 注入/刷新、错误码映射、SSE Job 客户端
- `src/config/workbench.ts` — 契约驱动设置分组、阶段、模块、后台分区
- `src/pages` — 登录 / 项目 / 设置 / 三栏工作台 / 外部评测 / 配置后台
- `src/components/workbench` — PipelineRail · StageCanvas · ModulePanel · QualityLoopPanel
