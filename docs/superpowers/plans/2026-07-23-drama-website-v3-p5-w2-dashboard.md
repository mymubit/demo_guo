# P5-W2 Dashboard Board + Search

Continuous SDD after P5-W1. Spec: `docs/superpowers/specs/2026-07-23-drama-website-v3-multikey-dashboard-design.md`

## Scope

DashboardPage only (no backend API change required unless list already supports filters).

1. View toggle: **列表** | **看板**
2. Board: columns by `stage` (use STAGE_LABEL); cards = projects in that stage
3. Search: text input filters by `title` (case-insensitive includes)
4. Keep existing: includeArchived checkbox, create, archive
5. Optional minimal: stage filter dropdown (nice-to-have if cheap)
6. Tests: DashboardPage unit tests for filter/view toggle
7. Baseline `docs/superpowers/baselines/2026-07-23-p5-w2-dashboard-board-acceptance.md`
8. Update roadmap both milestones complete

Do NOT touch payment. Do NOT git commit.
