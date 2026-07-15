# ScriptForge Workbench (PC)

React 18 + Vite + TypeScript strict 短剧创作工作台前端。

## 启动

仓库根目录一键：

```bash
npm run dev          # Docker 整栈
npm run dev:local    # 本机前端 + 后端
```

仅前端：

```bash
npm install
npm run dev
```

默认 `VITE_API_BASE_URL` 为空，开发态走 Vite 代理 `/api` → `http://localhost:8000`。

## Scripts

```bash
npm run test
npm run lint
npm run typecheck
npm run build
```

## Architecture

- `src/services` — Axios、Token、错误码、SSE
- `src/hooks/useWorkbenchDefinition` — 运行时加载 workbench-form
- `src/config/workbench.ts` — PC 宽度与 widget 映射
- `src/pages` / `src/components/workbench` — 登录、项目、三栏工作台
