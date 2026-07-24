# W3 Final Critical Fix — I1 / I2

日期：2026-07-23  
范围：W3 final review 两项 Important 修复（未 git commit）

## I1 — ScriptEditorPage 草稿 autosave 可靠性

**文件**
- `frontend/src/pages/ScriptEditorPage.tsx`
- `frontend/src/pages/ScriptEditorPage.test.tsx`

**变更**
- 用 refs 跟踪最新 `scenes` / `selectedEpisode` / `dirty`，`flushAutosave` 始终提交当前值。
- `putScriptDraft` 增加 `.catch()`：失败时保持 `dirty=true`，写入可见中文 `saveError`，并在 1s 后自动重试。
- 成功时仅在仍为同一集时清 `dirty`，并恢复「草稿自动保存」。
- `selectEpisode` 切集前若 dirty：先取消 debounce/retry timer，再 `await flushAutosave`；失败则留在当前集并展示错误。
- 状态文案：`saveError` → danger；否则 dirty →「正在保存…」；否则 →「草稿自动保存」。

**测试**
- 保留原 debounce autosave 用例并断言成功后状态文案。
- 新增：保存失败展示错误、保持脏状态并重试。
- 新增：切集前 flush 未保存编辑（fake timers）。

## I2 — `use_drafts` 刷新 memory_checkpoint

**文件**
- `backend/apps/drama/orchestrator/confirm.py`
- `backend/apps/drama/tests/test_v3_scripts_api.py`

**变更**
- `_commit_script_drafts` 在同一 atomic 路径中：提交新 `episode_scripts` 后，supersede 全部 committed+candidate `memory_checkpoint`。
- 优先深拷贝最新 committed/candidate checkpoint；若无则构造可过 schema 的最小 payload。
- 将 `episode` 设为合并后 scripts 的最大 `episode_number`；确保 `next_episode_constraints` 为 list，并追加（去重）「人工已修订正文，续写须对齐最新脚本」。
- `validate_artifact_payload` 通过后创建新 committed checkpoint；返回 `[scripts_id, checkpoint_id]`。

**测试**
- `test_confirm_use_drafts_validates_and_commits` 断言：新 committed checkpoint 存在、旧版 superseded、`episode==2`、schema 校验通过、`artifact_ids` 含两者。

## 验证结果

```text
# backend
py -3 manage.py test apps.drama.tests.test_v3_scripts_api --settings=config.settings.sqlite_test -v 1
→ Ran 9 tests … OK

# frontend
npm test -- src/pages/ScriptEditorPage.test.tsx
→ Tests 8 passed (8)

npm run typecheck
→ OK（tsc -b）
```
