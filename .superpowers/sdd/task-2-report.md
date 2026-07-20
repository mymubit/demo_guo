# Task 2 Report: Button 变体重命名（action / shell）

## Status

**完成** — Button 变体已从 `brand`/`gold` 迁移为 `action`/`shell`，TDD 测试通过，已提交。

## Commits

| SHA | Message |
|-----|---------|
| `b593297` | `feat(ui): replace brand button with action and shell variants` |

### 变更文件（3）

- `frontend/src/components/ui/Button.tsx` — 变体类型与样式重写
- `frontend/src/components/ui/button.test.tsx` — 新增（TDD）
- `frontend/src/components/workbench/QualityLoopPanel.tsx` — `brand` → `action`

## TDD 流程

1. **Red** — 新增 `button.test.tsx`，运行失败（仍为 `bg-brand-500`，无 `shell` 变体）
2. **Green** — 按 brief 模板实现 `Button.tsx`，迁移唯一 call site
3. **Verify** — `npx vitest run src/components/ui/button.test.tsx` → **2/2 PASS**

## 迁移摘要

| 旧值 | 新值 | 范围 |
|------|------|------|
| `variant="brand"` / 默认 `brand` | `variant="action"` / 默认 `action` | Button 组件 + QualityLoopPanel |
| `variant="gold"` | — | 全仓无 Button 使用 `gold`，无需迁移 |
| 壳层点缀 | `variant="shell"` | 新增变体；当前无 call site（AppShell 退出按钮仍为 `ghost`） |

`Badge tone="brand"` 等非 Button 引用未在本 Task 范围，留待后续 Task。

## 测试摘要

```
✓ button.test.tsx (2 tests) PASS
  - defaults to action variant classes
  - supports shell variant for chrome-only accents
```

`npm run typecheck` 仍有仓库既有错误（GenerationJobPanel SSE 类型、ExternalReviewPage FieldOption 等），**与本次 Button 变更无关**；无 `variant="brand"` 类型错误。

## Task 1 Minor（tailwind 注释）

检查 `frontend/tailwind.config.js` L33：`// 过渡期：旧 navy 类名仍可用，映射到 shell` — **已是可读中文，无需修复**，未纳入 commit。

## Concerns

- 无 `shell` 变体实际 call site；侧栏「回工作台」仍用 raw `bg-gold-400/15` 类名，后续 AppShell 视觉 Task 可统一。
- 全仓 typecheck 未绿，阻塞 CI 需其他 Task 处理。

## Review Fix（Important finding）

**问题**：`b593297` 在 `QualityLoopPanel.tsx` 中混入了与 Button 变体无关的 `complianceRiskTypeLabelZh` i18n 改动（import + 合规风险项渲染）。

**修复**：以 `git show b593297^:frontend/src/components/workbench/QualityLoopPanel.tsx` 为基线，仅保留 `variant="brand"` → `variant="action"` 变更；恢复 `uppercase text-amber-700` + `{item.type}` 原始渲染，移除 `reportLabels` import。

**新 commit**：`4972919` — `fix(ui): revert unrelated i18n hunks in QualityLoopPanel`

**验证**（2026-07-17）：

```
cd frontend; npx vitest run src/components/ui/button.test.tsx -v
✓ src/components/ui/button.test.tsx (2 tests) 48ms
Test Files  1 passed (1)
     Tests  2 passed (2)
```

**相对基线 diff 确认**（`git diff b593297^ -- QualityLoopPanel.tsx`）仅 1 行：`brand` → `action`。
