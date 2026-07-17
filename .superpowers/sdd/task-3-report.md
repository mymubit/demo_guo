# Task 3 Report: PromptBuilder 注入完整契约块

## Status
✅ Done — TDD red→green，4 个新测试全部通过，相关 SimpleTestCase 回归无破坏。

## Changes
- `backend/apps/drama/services/schema_prompt_contract.py`
  - 新增 `load_artifact_fixture(loader, artifact_key)`：通过 `SkillsBundleLoader.load_json` 读取 `build/fixtures/artifacts/valid-artifacts.json`，生产代码不再依赖 `apps.drama.tests.helpers`。
- `backend/apps/drama/services/prompt_builder.py`
  - `build()` 中加载 `artifact_schema` 与 `artifact_fixture`，调用 `render_contract_block` 生成嵌套必填路径 + 示例 JSON 的契约块，追加到 system prompt 的 `## 输出契约` 之后。
  - user prompt `output` 新增 `schema_required_paths`（完整嵌套路径列表），保留旧 `schema_required` 顶层列表作兼容。
  - 收缩 `_output_schema_hints`：删除与 schema 重复的 `必填字段: ...` 行及 `title / theme_code / matrix_key ...` 等硬编码清单，仅保留「禁止 schema 外字段」「synopsis 必须为对象」「six_stage_structure 恰好 6 项」等行为约束。
  - 新增 `_safe_load_artifact_schema` 容错 helper，schema 加载失败时降级为空契约块。
- `backend/apps/drama/tests/test_prompt_schema_injection.py`（新建）
  - 4 个 SimpleTestCase：episode-designer 锁定 `opening_hook` 嵌套路径与 JSON 键；story-bible 锁定 `surface_desire` / `characters[].arc.start`；user prompt 携带 `schema_required_paths`；project_brief 保留行为约束且不再出现顶层 `必填字段: title`。

## Test Summary
- 新增：`apps.drama.tests.test_prompt_schema_injection` — 4/4 PASS（0.539s）。
- 回归：`test_judge_prompt_injection` + `test_schema_prompt_contract` + 新测试 — 19/19 PASS（0.921s）。
- `test_generation` 等 TestCase 需要 PostgreSQL，本地无 DB 未跑；契约块逻辑独立，未触及 DB 路径。

## Commits
- `feat: inject nested schema field table and skeleton into role prompts`

## Concerns
- 本地无 PostgreSQL，依赖 DB 的 TestCase 未在本地验证；CI 中应可跑通。
- `_output_schema_hints` 仍保留少量与 schema 弱相关的行为约束（如 `compliance_risk` 枚举值），后续若 schema 已含 enum 可进一步收敛。
- `schema_required` 顶层列表保留作兼容，后续可由消费方迁移到 `schema_required_paths` 后移除。

## Report Path
c:\Users\99193\Desktop\demo_guo\.superpowers\sdd\task-3-report.md
