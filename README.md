# ScriptForge PC 创作工作台

面向短剧工业化创作的 PC 工作台。从零实现，不含旧版会员、订单、钱包或历史工作流。

## 技术栈

- 前端：React 18、TypeScript strict、Vite、Tailwind、TanStack Query
- 后端：Django、DRF、JWT、PostgreSQL
- 异步：Celery + Redis
- 技能：`drama-skills/` Git SSOT

## 启动（二选一）

### 1. Docker 整栈（推荐）

```bash
cp .env.example .env
npm run dev
# 等同 docker compose up --build
```

### 2. 本地一键（应用跑本机，库用本机或 Docker 基础设施）

本机已有 Postgres + Redis 时直接：

```bash
npm run dev:local
# 等同 ./scripts/dev-local.sh
```

没有本机库时，脚本会自动 `docker compose up -d postgres redis`，再起后端 / Celery / 前端。

常用选项：

```bash
./scripts/dev-local.sh --eager        # 不启 Celery worker，任务进程内同步
./scripts/dev-local.sh --no-frontend  # 只起后端
./scripts/dev-local.sh --infra-only   # 只确保库可用
```

地址：

- 前端 http://localhost:5173
- 后端 http://localhost:8000
- 健康检查 http://localhost:8000/health/

首次需要管理员：

```bash
# Docker
docker compose exec backend python manage.py createsuperuser

# 本地
cd backend && source .venv/bin/activate && python manage.py createsuperuser
```

## 测试

```bash
npm run test:real        # 独立 compose：真实 PG / Redis / Celery
npm run test:frontend
npm run lint:frontend
npm run build:frontend
npm run test:skills
```

## 真实 LLM

默认 `LLM_ENABLED=false`，任务标记为 `disabled`，不会用 Mock 冒充成功。联调时：

```env
LLM_ENABLED=true
LLM_API_BASE_URL=https://your-provider.example/v1
LLM_API_KEY=...
LLM_MODEL=...
```

## 导入脱敏数据

```bash
cd backend
python manage.py import_drama_dataset /path/to/dataset.json --owner demo --dry-run
python manage.py import_drama_dataset /path/to/dataset.json --owner demo
```

## 目录

```text
backend/       Django 领域后端
frontend/      PC 端 React 工作台
drama-skills/  技能、Schema、工作流与回归契约
scripts/       本地启动与真实基础设施测试
```
