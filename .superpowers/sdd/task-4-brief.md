### Task 4: 安装 shadcn 依赖并落地最小 primitive 集

**Files:**
- Modify: `frontend/package.json` / lockfile
- Create: `frontend/components.json`（若 CLI 生成）
- Create/Modify: `frontend/src/components/ui/input.tsx`、`dialog.tsx`、`table.tsx`、`dropdown-menu.tsx`（名称以 CLI 为准；若与现有 `Button.tsx` 冲突，保留现有 Button，勿覆盖 Task 2 变体）
- Modify: `frontend/tailwind.config.js` — 按需加 `tailwindcss-animate`

**Interfaces:**
- Consumes: Task 1 tokens（把 shadcn CSS 变量映射到 `--accent-action` 等）
- Produces: 可 import 的 Input/Dialog/Table/DropdownMenu；**不替换**业务页逻辑，仅备后续页换装使用

- [ ] **Step 1: Write the failing smoke test**

Create `frontend/src/components/ui/shadcn-smoke.test.tsx`:

```tsx
import { describe, expect, it } from 'vitest'

describe('shadcn primitives', () => {
  it('exposes Input module', async () => {
    const mod = await import('./input')
    expect(mod.Input).toBeTypeOf('function')
  })
})
```

- [ ] **Step 2: Run — expect FAIL（模块不存在）**

Run: `cd frontend && npx vitest run src/components/ui/shadcn-smoke.test.tsx -v`

- [ ] **Step 3: Install + generate**

在 `frontend/`：

```bash
npm install class-variance-authority @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-slot tailwindcss-animate
npx shadcn@latest init -y
npx shadcn@latest add input dialog table dropdown-menu -y
```

若 `shadcn add button` 会覆盖自定义 Button：**跳过 button**，保留 Task 2 文件。

在 `index.css` 的 `:root` 增加 shadcn 兼容映射（示例）：

```css
--background: var(--canvas);
--foreground: var(--ink);
--primary: var(--accent-action);
--primary-foreground: #ffffff;
--ring: var(--accent-action);
--border: var(--border);
--card: var(--surface);
```

`tailwind.config.js` 的 `plugins` 加入 `require('tailwindcss-animate')` 或 ESM `import tailwindcssAnimate from 'tailwindcss-animate'`。

- [ ] **Step 4: Run smoke + typecheck**

Run: `cd frontend && npx vitest run src/components/ui/shadcn-smoke.test.tsx -v && npm run typecheck`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/components.json frontend/src/components/ui frontend/src/styles/index.css frontend/tailwind.config.js
git commit -m "$(cat <<'EOF'
feat(ui): add shadcn primitives themed to action tokens

EOF
)"
```

---

