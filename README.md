# ScriptForge PC 创作工作台

面向短剧工业化创作的PC工作台。项目从零实现，不包含旧版会员、订单、钱包、旧角色或历史工作流。

## 技术栈

- 前端：React 18、TypeScript strict、Vite、Tailwind、TanStack Query
- 后端：Django、DRF、JWT、PostgreSQL
- 异步：Celery + Redis
- 技能：`drama-skills/` Git SSOT

## 启动

```bash
cp .env.example .env
docker compose up --build
```

- 前端：http://localhost:5173
- 后端：http://localhost:8000
- 健康检查：http://localhost:8000/health/

初始化用户：

```bash
docker compose exec backend python manage.py createsuperuser
```

## 真实基础设施测试

测试会启动独立 PostgreSQL、Redis、Celery Worker，执行迁移、Django测试和真实队列任务，不连接生产数据库。

```bash
npm run test:real
```

前端与技能契约：

```bash
npm run test:frontend
npm run lint:frontend
npm run build:frontend
npm run test:skills
```

## 真实LLM

默认 `LLM_ENABLED=false`，任务会明确标记为 `disabled`，不会用Mock冒充成功。联调真实模型时配置：

```env
LLM_ENABLED=true
LLM_API_BASE_URL=https://your-provider.example/v1
LLM_API_KEY=...
LLM_MODEL=...
```

生产前必须使用独立测试账号和费用上限执行完整原创、改编、质检与修复流程。

## 导入脱敏真实数据

数据文件使用当前 `project-settings`、`workflow-state` 和 artifact Schema，不保留旧字段兼容：

```bash
cd backend
python manage.py import_drama_dataset /path/to/dataset.json --owner demo --dry-run
python manage.py import_drama_dataset /path/to/dataset.json --owner demo
```

`--dry-run` 会执行真实数据库事务和全部Schema校验，最后回滚。

## 目录

```text
backend/       Django领域后端
frontend/      PC端React工作台
drama-skills/  技能、Schema、工作流与回归契约
scripts/       真实基础设施测试
```
