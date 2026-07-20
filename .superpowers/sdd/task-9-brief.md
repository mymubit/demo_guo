### Task 9: 工作台混合密度换装

**Files:**
- Modify: `frontend/src/pages/WorkbenchPage.tsx`
- Modify: `frontend/src/components/workbench/PipelineRail.tsx`
- Modify: `frontend/src/components/workbench/StageCanvas.tsx`
- Modify: `frontend/src/components/workbench/ModulePanel.tsx`
- Modify: `frontend/src/components/workbench/GenerationJobPanel.tsx`
- Modify: `frontend/src/components/workbench/QualityLoopPanel.tsx`
- Modify: `frontend/src/components/workbench/GenerationTroubleCard.tsx`
- Modify: `frontend/src/components/workbench/JobLlmCallLogsPanel.tsx`
- Modify: `frontend/src/components/theme/ThemeMatrixPicker.tsx`
- Modify: `frontend/src/components/artifacts/ArtifactViews.tsx`
- Modify: `frontend/src/components/artifacts/StoryBibleView.tsx`
- Create: `frontend/src/pages/workbench.tokens.test.ts`

**Interfaces:**
- Consumes: 现有 workbench 数据流与测试 fixtures
- Produces: 顶栏/PipelineRail 紧凑 + shell/gold 点缀允许；面板区冷雾 + action CTA；无 indigo

- [ ] **Step 1: Write failing scan + keep existing tests**

```ts
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const roots = [
  resolve(__dirname, 'WorkbenchPage.tsx'),
  resolve(__dirname, '../components/workbench'),
  resolve(__dirname, '../components/theme/ThemeMatrixPicker.tsx'),
]

describe('workbench tokens', () => {
  it('PipelineRail source has no indigo brand utilities', () => {
    const src = readFileSync(resolve(__dirname, '../components/workbench/PipelineRail.tsx'), 'utf8')
    expect(src).not.toMatch(/brand-500|bg-brand|text-brand/)
  })
})
```

- [ ] **Step 2: Run scan — FAIL if brand remains**

- [ ] **Step 3: Implement density split**

1. **紧凑顶区**（`WorkbenchPage` 顶栏 + `PipelineRail`）：减小 `py`/`gap`；当前阶段可用 `shell-accent` 指示（壳层语义的阶段条允许橙）。
2. **疏朗主区**（`StageCanvas`、`ModulePanel`、生成/质量面板）：`bg-canvas` 底 + `bg-surface` 面板 + `border-border`；主按钮 `action`。
3. 全局替换 workbench/artifacts/theme 内 `brand-*` → `action-*`。
4. 更新既有测试里若断言 class 含 `brand` 的期望。

- [ ] **Step 4: Run**

Run:

```bash
cd frontend && npx vitest run src/pages/workbench.tokens.test.ts src/components/workbench -v && npm run typecheck
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/WorkbenchPage.tsx frontend/src/pages/workbench.tokens.test.ts frontend/src/components/workbench frontend/src/components/theme/ThemeMatrixPicker.tsx frontend/src/components/artifacts
git commit -m "$(cat <<'EOF'
feat(workbench): hybrid density restyle with action and shell accents

EOF
)"
```

---

