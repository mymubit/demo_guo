# W3 Task 4 Review — 分集/正文编排（只读）

**Date:** 2026-07-23  
**Scope:** `orchestrator/{types,confirm,async_runner,dispatcher}.py` + `test_v3_episodes_async.py`  
**Tests:** `test_v3_episodes_async` — 6/6 OK（本地复跑）

---

## Verdicts

| 维度 | 结论 |
|------|------|
| **Spec** | ✅ |
| **Quality** | Approved |

---

## 6 Cases（brief）

| # | 用例 | 结论 |
|---|------|------|
| 1 | 无蓝图 `generate_episode_plan` → failed 人话 | ✅ executor `requires_committed` 拦截 brief+bible |
| 2 | 有蓝图 → generate → confirm → `stage=writing` | ✅ `confirm_episode_plan` 仅 `episodes→writing` |
| 3 | `revise_episode_plan` 仅改 ep2，ep1 不变 | ✅ merge 逻辑 + 测例断言 |
| 4 | `write_episode_batch` 1–2 → 两 key candidate | ✅ `episode_scripts` + `memory_checkpoint` |
| 5 | `confirm_script_candidate` → committed | ✅ 双 key committed，stage 保持 writing |
| 6 | 双 generate plan → confirm 后无残留 candidate | ✅ 旧 candidate superseded，confirm 清零 |

---

## 必查项

| 项 | 结论 | 依据 |
|----|------|------|
| **Confirm 推进 stage** | ✅ | `confirm_episode_plan`：`stage==episodes` 才 → `writing`；`confirm_script_candidate` 不改 stage |
| **Supersede** | ✅ | `_commit_candidates` 旧 committed/candidate 一并 superseded；executor 新 candidate 也 supersede 旧 candidate |
| **无 v6** | ✅ | orchestrator 改动文件零 `v6_*` 引用 |

---

## 备注（非阻塞）

1. `write_episode_batch` 缺分集计划 / 非法 `episode_range` 有实现（executor + `async_runner`），但未纳入 brief 6 测例。
2. `confirm_script_candidate` 按 key 取 latest candidate，未强制同 `command_run` 配对（正常 write 路径同 run 双写）。

---

## 实现摘要

- `types.py`：5 命令迁入 live/confirm，移出 stub
- `confirm.py`：新增 `confirm_episode_plan` / `confirm_script_candidate`
- `async_runner.py`：`write_episode_batch` 校验 `episode_range`；`V3_LLM_CALL_OVERRIDE` + eager 不变
- `dispatcher.py`：无需改动，路由已覆盖
