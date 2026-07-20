### Task 7: LoginPage 冷雾换装

**Files:**
- Modify: `frontend/src/pages/LoginPage.tsx`

**Interfaces:**
- Consumes: `Button variant="action"`；token 背景
- Produces: 无 indigo；主按钮海军蓝；轻纹理可用 navy/橙低透明

- [ ] **Step 1: Write failing visual-contract test**

Create `frontend/src/pages/LoginPage.tokens.test.tsx`:

```ts
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const src = readFileSync(resolve(__dirname, 'LoginPage.tsx'), 'utf8')

describe('LoginPage tokens', () => {
  it('does not reference indigo brand utilities', () => {
    expect(src).not.toMatch(/brand-500|brand-600|#6366f1/)
  })
})
```

- [ ] **Step 2: Run — FAIL if still has brand**

- [ ] **Step 3: Restyle**

- 背景径向渐变中的颜色改为 `rgba(10,22,40,…)` / `rgba(244,183,25,…)`（已有可保留），删除任何 indigo。
- 主提交按钮：`<Button type="submit" variant="action" loading={loading}>`。
- 卡片容器：`sf-panel` 或 `rounded-xl border border-border bg-surface`。
- 输入：`sf-control`。

- [ ] **Step 4: Run**

Run: `cd frontend && npx vitest run src/pages/LoginPage.tokens.test.tsx -v && npm run typecheck`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/LoginPage.tsx frontend/src/pages/LoginPage.tokens.test.tsx
git commit -m "$(cat <<'EOF'
feat(pages): restyle login to cold-mist action accents

EOF
)"
```

---

