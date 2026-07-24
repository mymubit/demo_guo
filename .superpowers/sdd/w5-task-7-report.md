# W5 Task 7 报告：前端 SystemPage

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W5 — 前端 SystemPage（GET/PUT `/api/v3/system/config/`）  
**Commits:** none（用户明确要求不 commit）  
**Brief:** `.superpowers/sdd/w5-task-7-brief.md`

---

## What I Implemented

### 1. `services/v3/system.ts`

- `getSystemConfig()` → `GET /api/v3/system/config/`
- `putSystemConfig(body)` → `PUT /api/v3/system/config/`，body `{ overlay, change_reason? }`
- 复用既有 `http` 信封解包；无新依赖

### 2. `pages/SystemPage.tsx`

对齐 QualityPage：`PageShell` + TanStack Query / Mutation。

- 展示 **当前生效配置** 摘要：修订号、平台中文名、评分预设中文名、及格阈值
- 表单：目标平台 / 评分预设 / 可选及格阈值 / 可选变更说明
- 保存写入 overlay；阈值留空则不写入 `quality_pass_threshold`
- 中文标签；无 operation ID / recipe 文案

### 3. 测试 `SystemPage.test.tsx`（5）

- 中文 UI、无 operation id
- effective 摘要中文标签
- 保存 platform + scoring_preset（无阈值）
- 可选阈值 + change_reason
- 加载失败展示错误

---

## Verification

```bash
cd frontend
npm test -- src/pages/SystemPage.test.tsx
npm run typecheck
```

**结果：** 5/5 passed；typecheck OK。

---

## Self-Review

- [x] GET/PUT `/api/v3/system/config/` 经 `services/v3/system.ts`
- [x] PageShell + TanStack Query，模式对齐 QualityPage
- [x] 中文 UI；无 operation ID
- [x] 无新依赖；未 commit

### Concerns（非阻塞）

1. **PUT 全量覆盖 overlay**：保存时始终提交当前表单的 platform + preset；阈值留空会清除既有阈值覆盖（回到预设默认）。符合后端「新 revision = 本次 overlay」语义。
2. **保存按钮在 PageShell actions**：通过 `form="system-config-form"` 关联表单；若浏览器对外部 submit 支持异常可改为表单内按钮。

---

## Files Touched

| 路径 | 操作 |
|------|------|
| `frontend/src/services/v3/system.ts` | 新建 |
| `frontend/src/pages/SystemPage.tsx` | 重写 |
| `frontend/src/pages/SystemPage.test.tsx` | 新建 |
| `.superpowers/sdd/w5-task-7-report.md` | 本报告 |

---

## Reviewer Checklist

| 必检项 | 结果 |
|--------|------|
| GET/PUT system/config 服务层 | ✅ |
| effective 摘要 + 表单保存 | ✅ |
| 中文标签 / 无 operation ID | ✅ |
| QualityPage 模式（PageShell + Query） | ✅ |
| `npm test` SystemPage + typecheck | ✅ 5/5 + OK |
| commit | ✅ 无 |

---

## Reviewer Verdict

**Spec:** ✅  
**Quality:** Approved

| 必检项 | 结论 |
|--------|------|
| 非占位 UI（生效摘要 + 表单） | ✅ `sf-panel` 摘要区 + 平台/预设/阈值/变更说明表单 |
| 保存配置（PUT overlay） | ✅ `putSystemConfig`；测试覆盖无阈值与含阈值+change_reason |
| 中文标签 | ✅ 标题、字段、选项、错误文案均为中文 |
| 无 operation ID | ✅ UI 无 recipe/op 文案；测试断言 `/operation\./i` |
| 测试 + typecheck | ✅ 独立复验 5/5 passed；typecheck OK |

**模式对齐：** PageShell + TanStack Query/Mutation + `formatApiError`，与 QualityPage 一致；`services/v3/system.ts` 对接 `GET/PUT /api/v3/system/config/`，类型与 OpenAPI 一致。

**非阻塞：** 阈值 0–100 客户端校验已实现但未单测；保存成功无 toast（与同类页一致）；`formatThreshold` 可简化。
