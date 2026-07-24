# ScriptForge V3 Backend

Django + DRF 应用层。产品 API 命名空间为 `/api/v3/`；旧 `/api/v2/**` 统一返回 HTTP 410（引导迁移到 V3）。Studio / V2 业务路由与页面已删除。

## Runtime

```bash
cd ..
docker compose up -d --build postgres redis backend celery
```

认证仍为基础设施能力，位于 `/api/v1/auth/`。业务创作 API 仅 `/api/v3/`。

## V3 API（摘录）

| Method | Path | Purpose |
|---|---|---|
| GET/POST | `/api/v3/projects/` | 项目列表与创建 |
| GET | `/api/v3/projects/{id}/` | 项目详情 |
| POST | `/api/v3/projects/{id}/archive/` | 归档项目 |
| * | `/api/v3/projects/{id}/topic/**` | 选题生成 / 草稿 / 确认 |
| * | `/api/v3/projects/{id}/blueprint/**` | 蓝图生成 / 确认 |
| * | `/api/v3/projects/{id}/episodes/**` | 分集计划 |
| * | `/api/v3/projects/{id}/scripts/**` | 正文撰写 |
| * | `/api/v3/projects/{id}/quality/**` | 质量 / 合规 / 接受问题 |
| * | `/api/v3/projects/{id}/delivery/**` | 交付打包 |
| * | `/api/v3/models/**` | 模型供应商与角色映射 |
| * | `/api/v3/logs/**` | 运行与调用日志 |
| GET/PUT | `/api/v3/system/config/` | 系统配置 |
| GET | `/api/v3/billing/plans/` | 套餐展示壳（只读，无支付） |
| POST | `/api/v3/commands/` | 命令分发（编排入口） |

完整路由见 `apps/drama/api/v3/urls.py`。

旧入口：

| Path | Behavior |
|---|---|
| `/api/v2/`、`/api/v2/**` | HTTP 410 Gone，提示使用 `/api/v3/` |

## Architecture（当前）

- `api/v3/`：HTTP 权限、参数与序列化
- `orchestrator/`：命令分发、确认、异步执行、交付门禁、系统配置
- `skills_bridge/`：配方映射与可注入 LLM 的生成执行
- `tasks_v3.py`：Celery 任务（`run_v3_command_task`）
- `models.py`：`V3Project` / `V3CommandRun` / `V3ArtifactVersion` 等持久化

## Tests

自包含设置不依赖本机 PostgreSQL / Redis：

```bash
# 在仓库根或 backend 下设置技能根目录
set DRAMA_SKILLS_ROOT=../drama-skills   # Windows PowerShell: $env:DRAMA_SKILLS_ROOT="..."

python manage.py test apps.drama.tests \
  --settings=config.settings.sqlite_test
```

真实 PG / Redis / Celery 闭环（Docker）：

```bash
# 仓库根目录
./scripts/test-real.sh
# 或：npm run test:real
```

该流程会执行 `scripts/verify_real_stack.py`（V3 orchestrator + Celery 烟测）。本地仅验证导入：

```bash
py -3 scripts/verify_real_stack.py --imports-only
```

## 环境要点

| 变量 | 说明 |
|---|---|
| `DRAMA_SKILLS_ROOT` | 指向仓库内 `drama-skills/`（技能 SSOT） |
| `LLM_ENABLED` | 默认 `false`；未配置供应商时生成命令会失败并写清错误 |
| `DJANGO_ENV` / DB / Redis | 见 `.env.example` 与 `config/settings/` |
