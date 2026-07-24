# W3 Task 3 审查：executor 分集/正文 JSON

**Date:** 2026-07-23  
**Scope:** `skills_bridge/executor.py`、`test_v3_episode_executor.py`（只读审查）  
**Verdict — Spec:** ✅  
**Verdict — Quality:** Approved

---

## Spec 对照

| 要求 | 结果 |
|------|------|
| `generate_episode_plan`：fake llm → 单对象 `episode_plan` candidate | ✅ `test_generate_episode_plan_with_fake_llm` |
| `revise_episode_plan`：fake llm → 局部 episodes 合并进 committed 拷贝 | ✅ `test_revise_episode_plan_merges_into_committed_copy` |
| revise 合并：范围外卡片不变 | ✅ `test_merge_keeps_out_of_range_cards_unchanged` + executor 集成断言 ep1 原样 |
| `write_episode_batch`：双产物 `{ episode_scripts, memory_checkpoint }` | ✅ `test_write_episode_batch_returns_scripts_and_checkpoint` |
| 缺 committed plan → 明确错误 | ✅ `test_revise_without_committed_plan_raises` |
| TDD / fake llm_call，无外网 | ✅ 5 用例均注入 `llm_call` |
| 回归 skills_bridge | ✅ 24/24 PASS（独立复验） |

---

## 实现要点

- **`merge_episode_plan_revision`**：深拷贝 committed，`episode_numbers` 过滤 LLM 卡片，按编号替换；顶层元数据保留。
- **`execute_generation`**：`revise_episode_plan` 在 `_map_payloads` 后、validate 前调用 `_apply_episode_plan_revision`。
- **`_map_payloads`**：单 write 整包映射；多 write 按键拆分（write batch 双产物路径已存在，本任务复用）。
- **`_build_prompt`**：注入 `request_payload`（revise 的 `episode_numbers` / write 的 `episode_range`）。

---

## 质量备注（非阻塞）

1. 未单测「LLM 返回编号不在 `episode_numbers` 内时被忽略」——合并函数有 `continue` 分支，行为合理。
2. `episode_numbers` 为空时替换 LLM 返回的全部编号（报告已说明，Task 4 编排层再约束）。
3. 编排 live 命令 / confirm / stage 推进属 Task 4，本任务范围正确。

---

## 验证

```text
py -3 manage.py test apps.drama.tests.test_v3_episode_executor apps.drama.tests.test_v3_skills_bridge --settings=config.settings.sqlite_test
→ 24 tests, OK (~5.4s)
```
