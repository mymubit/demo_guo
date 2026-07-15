# ScriptForge Drama Backend

生产可用、结构精简的 Django + DRF 后端，契约以 `DRAMA_SKILLS_ROOT` 下 manifest / schemas / api-contract 为唯一真相。

## 快速开始

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env，至少配置 PostgreSQL 与 DRAMA_SKILLS_ROOT

export DJANGO_ENV=development
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

## Celery Worker

```bash
celery -A config worker -l info
```

集成环境由根目录 `docker-compose` 启动真实 Redis worker；单测使用 `CELERY_TASK_ALWAYS_EAGER=true`。

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

认证：`POST /api/v1/auth/token/`、`POST /api/v1/auth/register/`。

健康检查：`GET /health/`。

## 测试

```bash
export DJANGO_ENV=test
export DRAMA_SKILLS_ROOT=/workspace
python manage.py test apps.drama.tests -v 2
```

测试依赖真实 PostgreSQL / Redis（见 `.env.example`），不访问外网；`LLM_ENABLED=false` 时生成任务标记为 `disabled`，不以 mock 冒充成功。

## 架构要点

- **apps/core**：统一响应 `{code,message,data}`、异常处理、审计日志、健康检查、JSON Schema 校验
- **apps/users**：Django 内置 User + SimpleJWT
- **apps/drama**：模型、服务层（SkillsBundleLoader / ProjectSettings / Workflow / Artifact / ConfigOverlay / Generation）、Celery 任务、DRF 权限类
- **乐观锁**：项目设置 `settings_revision`、工作流 `version`、配置 `audit.revision`，均通过 `If-Match` 头传递
- **LLM**：`LLM_API_BASE_URL` + `LLM_API_KEY` OpenAI 兼容 HTTP；`LLM_ENABLED=false` 显式禁用
