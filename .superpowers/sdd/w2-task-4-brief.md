### Task 4: 异步编排 + Celery 任务

**Files:**
- Modify: `backend/apps/drama/orchestrator/types.py` — 从 `ASYNC_STUB_COMMANDS` 移除四条 W2 命令；新增 `ASYNC_LIVE_COMMANDS`、`SYNC_CONFIRM_COMMANDS`
- Modify: `backend/apps/drama/orchestrator/dispatcher.py`
- Create: `backend/apps/drama/orchestrator/async_runner.py`
- Create: `backend/apps/drama/tasks_v3.py`
- Create: `backend/apps/drama/orchestrator/confirm.py`
- Test: `backend/apps/drama/tests/test_v3_async_commands.py`

**Interfaces:**
- `dispatch_command` 对 `generate_topic_brief` / `generate_blueprint`：
  1. 校验 `payload.project_id` 且项目属主
  2. 创建 run `queued`，绑定 project
  3. 调用 `enqueue_v3_command(run.id)` → Celery
  4. 立即返回 run（status=`queued`）
- `run_v3_command_task(run_id)`：
  1. 置 `running`
  2. `execute_generation(...)`
  3. `succeeded` + `result_payload={artifact_ids:[...]}`；失败则 `failed` + `error_message` 人话
- `confirm_topic_brief` / `confirm_blueprint`：**同步**，实现于 `confirm.py`：
  - payload: `{project_id, artifact_version_ids?: []}`；默认取各 key 最新 candidate
  - 将 candidate → committed；同 key 旧 committed → superseded
  - 更新 stage（topic→blueprint / blueprint→episodes）
  - 蓝图确认必须五产物齐全，否则 failed

- [ ] **Step 1: 测试（ALWAYS_EAGER + mock llm_call 注入点）**

注入策略：在 `async_runner` 读取 `settings.V3_LLM_CALL_OVERRIDE` 可调用对象（仅测试 settings 设置），生产为 `None`。

用例：
1. generate_topic_brief → eager 后 succeeded + 1 candidate
2. confirm_topic_brief → committed + stage blueprint
3. generate_blueprint 无 brief → failed 人话
4. generate_blueprint 有 brief → 5 candidates
5. confirm_blueprint → stage episodes
6. grep 保障：`orchestrator`/`skills_bridge`/`tasks_v3` 文件文本不含 `v6_runtime`

- [ ] **Step 2–4: 实现至 PASS**；更新 `_UNSUPPORTED_MESSAGE` 仅对仍 stub 的命令

---

