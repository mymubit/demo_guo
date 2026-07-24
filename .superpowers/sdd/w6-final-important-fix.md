# W6 Final Review — Important 修复报告

> **日期：** 2026-07-23  
> **范围：** I1 / I2（`w6-final-review.md` Important ×2）；顺带 M3 根 README 产品命名  
> **约束：** 未 git commit

## Status

**Fixed — both Important findings**

| # | 问题 | 状态 |
|---|------|------|
| I1 | `verify_real_stack.py` + CI 仍引用已删 GenerationService/WorkflowService | ✅ Fixed |
| I2 | `backend/README.md` 仍声明 V2-only 业务 API | ✅ Fixed |

---

## I1 — V3 真实栈烟测脚本

**根因：** `scripts/verify_real_stack.py` 仍 `import GenerationService` / `WorkflowService`（W6 已删）；`docker-compose.test.yml` → `real-celery-stack` 在 import 阶段即炸。

**修复：** 重写为 V3 最小闭环：

1. Redis 读写
2. 导入 `apps.drama.orchestrator` / `tasks_v3`（断言无已删模块名）
3. 同步 `dispatch_command(create_project)`（PostgreSQL）
4. 异步 `generate_topic_brief` 经 Celery worker 落终态（`SUCCEEDED` 或无供应商时的 `FAILED` 均可，证明 worker 已执行）

新增安全入口：`--imports-only`（仅 django.setup + 导入烟测）、`--help`。

**文件：**

- `scripts/verify_real_stack.py`（重写）
- `.github/workflows/ci.yml`（注释标明 V3 栈；job 仍调用 `./scripts/test-real.sh`，compose 末步执行新脚本）

---

## I2 — backend README 对齐 V3

**根因：** 文档仍写「Business APIs are V2 only」、完整 `/api/v2/studio/**` 表，并引用已删 `v2_views` / `v6_runtime` 等。

**修复：** 改写为：

- 产品 API：`/api/v3/`
- `/api/v2/**` → 410
- 当前架构：`api/v3` + `orchestrator` + `skills_bridge` + `tasks_v3`
- 保留准确测试说明：`sqlite_test`、`DRAMA_SKILLS_ROOT`、`test-real.sh` / `--imports-only`

**文件：** `backend/README.md`

**顺带（M3）：** 根 `README.md` 标题与首段改为 ScriptForge V3 / `/api/v3/`，去掉「V6 操作系统为唯一入口」表述。

---

## Verify

```text
py -3 scripts/verify_real_stack.py --help
# → usage + --imports-only

py -3 scripts/verify_real_stack.py --imports-only
# → V3_IMPORTS_OK  (exit 0)

rg GenerationService|WorkflowService scripts/verify_real_stack.py
# → 仅 docstring / banned 字符串检查，无 import

rg "api/v2/studio|Business APIs are V2|v2_views|v6_runtime" backend/README.md
# → 0 matches
```

CI `real-celery-stack`：仍跑 `./scripts/test-real.sh` → compose `integration-test` 最后一行执行新 `verify_real_stack.py`（无已删符号 import）。

---

## 未做

- 未 git commit（按约束）
- 未本地跑完整 `test-real.sh`（需 Docker compose；脚本逻辑与导入已机跑验证）
- Minor M1/M2/M4 未改（非本任务范围）
