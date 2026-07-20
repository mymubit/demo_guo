### Task 10: 工具域 + 运维域页面

**Files:**
- Modify: `frontend/src/pages/ExternalReviewPage.tsx`
- Modify: `frontend/src/pages/ExternalReviewRecordsPage.tsx`
- Modify: `frontend/src/pages/ModelHubPage.tsx`
- Modify: `frontend/src/pages/LlmLogsPage.tsx`
- Modify: `frontend/src/pages/AdminConfigPage.tsx`
- Modify: `frontend/src/pages/SkillOpsPage.tsx`
- Create: `frontend/src/pages/ops-tools.tokens.test.ts`

**Interfaces:**
- Consumes: `PageShell`、表格冷雾、`action` CTA
- Produces: 六页无 indigo；日志页保持高信息密度但底色仍为冷雾（非全暗）

- [ ] **Step 1: Write scan test**

```ts
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const files = [
  'ExternalReviewPage.tsx',
  'ExternalReviewRecordsPage.tsx',
  'ModelHubPage.tsx',
  'LlmLogsPage.tsx',
  'AdminConfigPage.tsx',
  'SkillOpsPage.tsx',
]

describe('ops-tools pages tokens', () => {
  for (const file of files) {
    it(`${file} has no indigo brand classes`, () => {
      const src = readFileSync(resolve(__dirname, file), 'utf8')
      expect(src).not.toMatch(/brand-500|brand-600|bg-brand|text-brand|tone=\"brand\"|variant=\"brand\"/)
    })
  }
})
```

- [ ] **Step 2: Run — FAIL then fix**

- [ ] **Step 3: Restyle**

- 统一 `PageShell` + `sf-panel` / `border-border bg-surface`。
- 表格：表头 `text-ink-muted`；行 hover `bg-canvas-muted/60`；选中行可用 `bg-action/5`。
- 主按钮 `action`；可用 Task 4 的 `Table`/`Dialog` 替换手写表格壳（**可选**，若改动面过大则只换 class）。
- 不改 API hooks。

- [ ] **Step 4: Run**

Run: `cd frontend && npx vitest run src/pages/ops-tools.tokens.test.ts -v && npm run typecheck && npm run test`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/ExternalReviewPage.tsx frontend/src/pages/ExternalReviewRecordsPage.tsx frontend/src/pages/ModelHubPage.tsx frontend/src/pages/LlmLogsPage.tsx frontend/src/pages/AdminConfigPage.tsx frontend/src/pages/SkillOpsPage.tsx frontend/src/pages/ops-tools.tokens.test.ts
git commit -m "$(cat <<'EOF'
feat(pages): cold-mist restyle for tools and ops domains

EOF
)"
```

---

