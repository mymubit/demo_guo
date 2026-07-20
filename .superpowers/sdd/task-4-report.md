# Task 4 Report: 安装 shadcn 依赖并落地最小 primitive 集

## Status

**完成** — npm 依赖已装；`npx shadcn@latest init` 在 Windows 上挂起后改为手写 Radix 封装（new-york 风格）；**未**执行 `shadcn add button`，保留 Task 2 `Button.tsx`；CSS 变量映射到 dual-accent tokens；smoke 测试 GREEN。

## Commits

| SHA | Message |
|-----|---------|
| `88bbdd0` | `feat(ui): add shadcn primitives themed to action tokens` |

### 变更文件

- `frontend/package.json` / `package-lock.json` — cva、Radix dialog/dropdown-menu/slot、tailwindcss-animate
- `frontend/components.json` — 手写 shadcn 配置（aliases → `@/utils/cn`）
- `frontend/src/components/ui/input.tsx` — Input（函数组件，满足 smoke `typeof function`）
- `frontend/src/components/ui/dialog.tsx` — Dialog 族
- `frontend/src/components/ui/table.tsx` — Table 族
- `frontend/src/components/ui/dropdown-menu.tsx` — DropdownMenu 族
- `frontend/src/components/ui/shadcn-smoke.test.tsx` — TDD smoke
- `frontend/src/styles/index.css` — shadcn CSS 变量 → `--canvas` / `--accent-action` 等
- `frontend/tailwind.config.js` — semantic colors + `tailwindcss-animate`

**未改动**：`frontend/src/components/ui/Button.tsx`（Task 2 变体完整保留）。

## TDD 流程

1. **Red** — `shadcn-smoke.test.tsx` → FAIL（`./input` 模块不存在）
2. **Install** — `npm install class-variance-authority @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-slot tailwindcss-animate`
3. **CLI** — `npx shadcn@latest init -y --defaults` 卡住（>50s 无输出）→ 终止，手写等价组件
4. **Green** — Input/Dialog/Table/DropdownMenu + token 映射 → smoke **1/1 PASS**
5. **Verify** — `src/components/ui` 全部测试 **5/5 PASS**（含 button / badge-tabs）

## 测试摘要

```
✓ shadcn-smoke.test.tsx (1) — exposes Input module
✓ button.test.tsx (2)
✓ badge-tabs.test.tsx (2)
```

`npm run typecheck` 仍有仓库既有错误（StageCanvas `onJobUpdate`、ExternalReviewPage `FieldOption`、themeLabels 等），**与本次 primitive 无关**；`components/ui/{input,dialog,table,dropdown-menu}` 无新增 TS 报错。

## Concerns

- shadcn CLI 在本机 PowerShell 交互/挂起，后续加组件建议继续手写或改用非交互 CI 环境。
- Input 为函数组件（非 `forwardRef`），以便 smoke 断言 `typeof function`；若后续需 ref，可再改并用测试适配。
- 全仓 typecheck 未绿，阻塞 CI 需其他 Task 处理。
