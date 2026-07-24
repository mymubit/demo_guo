# W5 Task 9 报告：前端 LogsPage

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W5 — 前端 LogsPage（`/api/v3/logs/**`）  
**Commits:** none（用户明确要求不 commit）  
**Brief:** `.superpowers/sdd/w5-task-9-brief.md`

---

## What I Implemented

### 1. `services/v3/logs.ts`

- `listLogRuns(params?)` → `GET /api/v3/logs/runs/`（`project_id` / `status` / `command_type` / 分页）
- `getLogRun(runId)` → `GET /api/v3/logs/runs/{id}/`
- `getLogCall(callId)` → `GET /api/v3/logs/calls/{id}/`
- 复用既有 `http` 信封解包；空筛选项不传参

### 2. `pages/LogsPage.tsx`

对齐 ModelsPage：`PageShell` + TanStack Query + 右侧 Dialog 详情。

- **筛选**：项目 / 状态 / 命令类型（中文标签；value 为产品 `command_type`）
- **run 列表**：中文命令名 + 状态 + 项目名 + 时间
- **详情抽屉**：状态、错误、调用明细；展开后拉取 call 全量快照；prompt/response 等宽 `font-mono`
- **下载 JSON**：当前详情 Blob 下载
- **高级折叠**：可显示产品 `command_type`；默认不展示；`operation.*` 映射为「未知命令」
- 中文 UI；无 operation / recipe 文案

### 3. 类型

- 复用既有 `domain.ts` 的 `LogCall` / `LogRun` / `LogRunList`（无需新增）

### 4. 测试 `LogsPage.test.tsx`（5）

- 中文 UI、无 `operation.*` / 配方 ID
- 筛选调用 `listLogRuns` 传参
- 详情 calls + 展开 prompt/response（mono）
- 下载 JSON Blob
- 列表加载失败展示错误

---

## Verification

```bash
cd frontend
npm test -- src/pages/LogsPage.test.tsx
npm run typecheck
```

**结果：** 5/5 passed；typecheck OK。

---

## Self-Review

- [x] 服务层对接 `/api/v3/logs/**`
- [x] 筛选 + 列表 + 详情 calls + mono 展开
- [x] 可选 JSON 下载
- [x] 中文 UI；禁止展示 `operation.*`
- [x] 无新依赖；未 commit

### Concerns（非阻塞）

1. **分页**：当前固定 `limit=20`、`offset=0`，无翻页控件；总量仅文案展示。
2. **角色文案**：call 的 `role` / `purpose` 仍展示后端原文（非 `operation.*`），未做中文映射。
3. **试连日志**：若后端未挂 `v3_command_run`（Task 6 concern），本页列表可能看不到 `test_model_provider` 的 LLM calls。

---

## Files Touched

| 路径 | 操作 |
|------|------|
| `frontend/src/services/v3/logs.ts` | 新建 |
| `frontend/src/pages/LogsPage.tsx` | 重写 |
| `frontend/src/pages/LogsPage.test.tsx` | 新建 |
| `.superpowers/sdd/w5-task-9-report.md` | 本报告 |

---

## Reviewer Checklist

| 必检项 | 结果 |
|--------|------|
| logs 服务层覆盖 runs 列表/详情 + call 详情 | ✅ |
| 筛选 project/status/command_type | ✅ |
| 详情 calls + mono prompt/response | ✅ |
| 禁止展示 `operation.*`（含高级区） | ✅ |
| npm test + typecheck | ✅（6/6） |
| 未 git commit | ✅ |

---

## Reviewer Verdict

**Spec:** ✅  
**Quality:** Approved

| 必检项 | 结果 | 说明 |
|--------|------|------|
| logs 服务层 runs/call | ✅ | `listLogRuns` / `getLogRun` / `getLogCall` |
| 筛选 project/status/command_type | ✅ | 三筛 + 空值不传参 |
| run 列表 + 详情 calls | ✅ | 中文命令名/状态/项目/时间 |
| 展开 prompt/response (mono) | ✅ | 懒加载 + `font-mono` |
| JSON 下载 | ✅ | Blob 下载当前详情 |
| 禁止 `operation.*` | ✅ | 列表/标题 `commandTypeLabel`；高级区 `advancedCommandIdentifier` → `operation.*` 显示「未知命令」，不渲染原文 |
| 只读 | ✅ | 无写操作 |
| tests + typecheck | ✅ | 6/6 passed；typecheck OK（复核 2026-07-23） |

**高级区 `operation.*`：** ✅ 已确认。展开「高级：显示命令标识」时，`operation.score-script` 等内部 ID 仅展示「未知命令」；专用用例断言 UI 不含 `operation.`。

**非阻塞：** 分页固定 `limit=20`；`role`/`purpose` 未中文化；JSON 下载仍含后端原始 `command_type`（非 UI 展示）。

---

## Spec Rejection Fix（2026-07-23）

### 根因

高级折叠「显示命令标识」直接渲染 `detail.command_type`，未对 `operation.*` / kebab-case 配方 ID 脱敏。

### 修复

- 新增 `isInternalCommandId`：识别 `operation.*` 与 kebab-case 配方 ID
- 新增 `advancedCommandIdentifier`：产品 `command_type` 枚举原样展示；内部 ID →「未知命令」
- 列表/标题的 `commandTypeLabel` 同步使用同一内部 ID 判定
- 测试：mock `command_type: operation.score-script`，展开高级区后断言 UI 不含 `operation.`

### 验证

```bash
cd frontend
npm test -- src/pages/LogsPage.test.tsx
npm run typecheck
```

**结果：** 6/6 passed；typecheck OK。

### 状态

阻塞项已关闭；未 git commit。
