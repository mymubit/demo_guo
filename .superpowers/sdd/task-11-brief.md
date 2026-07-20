### Task 11: 全仓清理与验收

**Files:**
- Modify: 任何仍含 `brand-` / `#6366f1` 的 `frontend/src/**`
- Modify: `docs/superpowers/specs/2026-07-17-frontend-visual-rewrite-design.md`（若需勾验收）
- Create: `frontend/src/styles/no-indigo.test.ts`

**Interfaces:**
- Consumes: Task 1–10
- Produces: 仓库级无 indigo 主色引用；验收命令全绿

- [ ] **Step 1: Write repo-wide guard test**

```ts
import { execSync } from 'node:child_process'
import { describe, expect, it } from 'vitest'

describe('no indigo brand leftovers', () => {
  it('rg finds no brand-500 utility in src', () => {
    let out = ''
    try {
      out = execSync('rg -n "brand-500|#6366f1|bg-brand-|text-brand-" src', {
        cwd: resolveFrontendRoot(),
        encoding: 'utf8',
      })
    } catch (e) {
      // rg exit 1 = no matches
      const err = e as { status?: number; stdout?: string }
      if (err.status === 1) {
        expect(err.stdout ?? '').toBe('')
        return
      }
      throw e
    }
    expect(out).toBe('')
  })
})

function resolveFrontendRoot(): string {
  return new URL('../..', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1')
}
```

若 Windows 上 `rg`/`import.meta.url` 路径不稳，改用 vitest + `fs` 递归扫描 `frontend/src`（实现时选可稳定跑通的写法）。

- [ ] **Step 2: Run — FAIL on leftovers, then delete/replace**

- [ ] **Step 3: Final verification commands**

```bash
cd frontend
npm run typecheck
npm run lint
npm run test
npm run build
```

Expected: 全部 exit 0。

手测清单（执行者勾选）：

- [ ] 登录 → 项目列表（侧栏橙 active，新建按钮海军蓝）
- [ ] 新建项目 / 设置
- [ ] 工作台阶段条 + 生成面板
- [ ] 外部评测 + 记录
- [ ] 模型管理 / LLM 日志 / 技能覆盖 / 技能运维

- [ ] **Step 4: Commit**

```bash
git add -u frontend docs/superpowers/specs/2026-07-17-frontend-visual-rewrite-design.md
git commit -m "$(cat <<'EOF'
chore(ui): purge indigo leftovers and lock visual rewrite acceptance

EOF
)"
```

---

## Self-Review

1. **Spec coverage:** token、双色、壳层、冷雾页、工作台混合、shadcn+自研、全页清单、方案 A 波次、非 Figma 门禁、验收命令均有对应 Task。
2. **Placeholder scan:** 无 TBD；Task 4 CLI 命令为明确默认；Task 11 Windows rg 提供了备用扫描策略。
3. **Type consistency:** `Button`/`Badge` 使用 `action`/`shell`；CSS 变量名与规格 §4 一致。

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-07-17-frontend-visual-rewrite.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — 每个 Task 派新生 subagent，Task 间两阶段审查，迭代快

**2. Inline Execution** — 本会话用 executing-plans 按 Task 推进，设检查点

**Which approach?**

