### Task 8: 创作域页面（列表 / 新建 / 设置）

**Files:**
- Modify: `frontend/src/pages/ProjectListPage.tsx`
- Modify: `frontend/src/pages/NewProjectPage.tsx`
- Modify: `frontend/src/pages/ProjectSettingsPage.tsx`
- Create: `frontend/src/pages/create-domain.tokens.test.ts`

**Interfaces:**
- Consumes: `PageShell`、`Button action`、`Badge action`、冷雾面板
- Produces: 三页无 `brand-*`；列表主 CTA「新建项目」为 `action`

- [ ] **Step 1: Write failing scan test**

```ts
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const files = ['ProjectListPage.tsx', 'NewProjectPage.tsx', 'ProjectSettingsPage.tsx']

describe('create-domain pages tokens', () => {
  for (const file of files) {
    it(`${file} has no indigo brand classes`, () => {
      const src = readFileSync(resolve(__dirname, file), 'utf8')
      expect(src).not.toMatch(/brand-500|brand-600|bg-brand|text-brand|tone=\"brand\"|variant=\"brand\"/)
    })
  }
})
```

- [ ] **Step 2: Run — expect FAIL on pages still using brand**

- [ ] **Step 3: Restyle each page**

统一规则（三页都执行）：

1. 所有 `bg-brand-*` / `text-brand-*` / `ring-brand-*` → `action` 等价类。
2. 主按钮默认 `action`；危险操作用 `danger`。
3. 列表：项目行用 `sf-panel` 或 `border-border bg-surface`；增加疏朗 `gap`；状态 Badge 用 `action`/`success`/`default`。
4. 新建/设置：表单控件统一 `sf-control` / shadcn `Input`；分区标题 `sf-section-title`。
5. **不改** `dramaApi` 调用与字段。

- [ ] **Step 4: Run**

Run: `cd frontend && npx vitest run src/pages/create-domain.tokens.test.ts -v && npm run typecheck && npm run test`

Expected: 全绿或仅与本域无关的既有失败需先记录——本任务不得引入新失败。

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/ProjectListPage.tsx frontend/src/pages/NewProjectPage.tsx frontend/src/pages/ProjectSettingsPage.tsx frontend/src/pages/create-domain.tokens.test.ts
git commit -m "$(cat <<'EOF'
feat(pages): cold-mist restyle for project create domain

EOF
)"
```

---

