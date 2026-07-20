# Task 1 Report: Design Token + Tailwind 映射

## Status: DONE

## Commits

| SHA | Subject |
|-----|---------|
| `14b9fc3` | feat(ui): introduce dual-accent design tokens |

## Files Changed

| File | Action |
|------|--------|
| `frontend/src/styles/index.css` | Modified — replaced `:root` CSS variables, updated `@layer components` to use new token-based Tailwind classes |
| `frontend/tailwind.config.js` | Modified — replaced `theme.extend.colors` with shell/action/canvas/surface/ink mapping; removed `brand` palette; kept transitional `navy`/`gold` |
| `frontend/src/styles/tokens.test.ts` | Created — source-file assertions for dual-accent tokens and indigo brand removal |

## TDD Evidence

### RED (Step 2)

```
npx vitest run src/styles/tokens.test.ts -v
```

```
❯ src/styles/tokens.test.ts (2 tests | 2 failed)
  × design tokens > defines dual accents and cold mist canvas
    → expected '...' to contain '--accent-shell: #f4b719'
  × design tokens > does not keep indigo brand-500 as system brand
    → expected '...' not to contain '--brand-500: #6366f1'
```

Both failures were for the expected reasons: new CSS variables absent, legacy `--brand-500: #6366f1` still present.

### GREEN (Step 4)

```
npx vitest run src/styles/tokens.test.ts -v
```

```
✓ src/styles/tokens.test.ts (2 tests) 2ms
 Test Files  1 passed (1)
      Tests  2 passed (2)
```

## Typecheck

```
npm run typecheck
```

**Result:** FAIL — 26 pre-existing TS errors in unrelated files (GenerationJobPanel, ExternalReviewPage, NewProjectPage, etc.). None relate to token/CSS changes. Per brief, deferred to later tasks.

## Self-Review

### What was implemented

1. **CSS variables (`:root`)** — dual-accent system:
   - Shell: `--shell-bg`, `--shell-bg-elevated`, `--shell-ink`, `--shell-ink-muted`, `--accent-shell`, `--accent-shell-hover`
   - Canvas: `--canvas` (#eef1f5 cold mist), `--canvas-muted`, `--surface`, `--border`
   - Action: `--accent-action`, `--accent-action-hover`, `--focus-ring`
   - Ink: `--ink`, `--ink-muted`, `--ink-faint`
   - Semantic: `--danger`, `--success`, `--warning`

2. **Tailwind color mapping** — `shell`, `action`, `canvas`, `surface`, `border`, `ink`, `danger`, `success`, `warning` all reference CSS variables.

3. **Transitional aliases** — `navy.900/800` → shell vars; `gold.300/400` → accent-shell vars. Old `brand` palette removed from Tailwind config.

4. **Component layer** — `.sf-control`, `.sf-panel` updated to use `border-border`, `bg-surface`, `focus:border-action` (no page/Button/AppShell restyle).

### Scope compliance

- Only the 3 files listed in the brief were changed.
- No page components, Button, or AppShell restyled.
- Downstream `brand-*` class references in TSX remain (expected until Task 2–3).

### Concerns

None blocking. Typecheck failures are pre-existing WIP, not introduced by this task.

## Next Steps (downstream tasks)

- Task 2–3: migrate `brand-*` references in components to `action`/`shell` classes.
- Task 4+: restyle AppShell, Button, pages using new tokens.
