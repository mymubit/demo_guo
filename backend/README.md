# ScriptForge Drama Backend

Django + DRF 后端，契约以 `DRAMA_SKILLS_ROOT` 下 manifest / schemas / api-contract 为唯一真相。

## 启动

仓库根目录一键即可（推荐）：

```bash
# Docker 整栈
npm run dev

# 或本机进程 + 本机/Docker 基础设施
npm run dev:local
```

仅后端调试时：

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 按需改 DB / Redis；DRAMA_SKILLS_ROOT 默认 ../drama-skills
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
# 另开终端：celery -A config worker -l info
# 或不启 worker：CELERY_TASK_ALWAYS_EAGER=true
```

## API 概览

| 方法 | 路径 | 权限 |
|------|------|------|
| GET/POST | `/api/v1/drama/projects/` | 登录 |
| GET/PUT/DELETE | `/api/v1/drama/projects/{id}/` | project.read/write |
| GET/PUT | `/api/v1/drama/projects/{id}/settings/` | project.read/write + If-Match |
| GET | `/api/v1/drama/projects/{id}/workflow/` | project.read |
| POST | `/api/v1/drama/projects/{id}/workflow/commands/` | project.execute |
| POST | `/api/v1/drama/projects/{id}/approvals/story-bible/` | project.approve |
| GET | `/api/v1/drama/projects/{id}/artifacts/{key}/` | project.read |
| POST | `/api/v1/drama/projects/{id}/generation/start/` | project.execute |
| GET | `/api/v1/drama/projects/{id}/generation/{job_id}/` | project.read |
| GET | `/api/v1/drama/projects/{id}/generation/{job_id}/stream/` | SSE |
| POST | `/api/v1/drama/external-script-reviews/` | project.execute |
| GET/PUT | `/api/v1/drama/admin/config/` | drama_config.* |
| POST | `/api/v1/drama/admin/config/rollback/` | drama_config.rollback |

认证：`POST /api/v1/auth/token/`、`POST /api/v1/auth/register/`。健康检查：`GET /health/`。

## 测试

```bash
export DJANGO_ENV=test
python manage.py test apps.drama.tests -v 2
```

依赖真实 PostgreSQL / Redis；`LLM_ENABLED=false` 时生成任务标记为 `disabled`。

## 架构要点

- **apps/core**：统一响应、异常、审计、健康检查、JSON Schema
- **apps/users**：Django User + SimpleJWT
- **apps/drama**：Skills 加载、项目设置、工作流、产物、配置覆盖、生成任务
- **乐观锁**：settings_revision / workflow version / config revision，经 `If-Match` 传递
