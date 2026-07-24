# W6 Task 7 Brief

Plan Task 7: §8 全量回归基线

Create: `docs/superpowers/baselines/2026-07-23-w6-billing-legacy-cut-acceptance.md`
Modify: `docs/superpowers/plans/2026-07-22-drama-website-v3.md` — W6 ✅; note phase-1 complete
Update: `.superpowers/sdd/progress-w6.md`

**Actually run:**

```bash
cd backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests --settings=config.settings.sqlite_test -v 1
```

If some tests fail due to deleted modules still being imported elsewhere, fix minimally OR exclude only clearly obsolete modules and document — prefer fix imports so full suite green.

```bash
cd frontend
npm test
npm run typecheck
```

```bash
rg "v6_runtime|v6_workbench|v6_control_plane|/api/v2/studio" backend/apps/drama/orchestrator backend/apps/drama/skills_bridge backend/apps/drama/api/v3 backend/apps/drama/tasks_v3.py frontend/src/app frontend/src/pages
rg "from apps.drama.v2|GenerationService" backend/apps/drama --glob "!migrations/**"
```

Baseline must check Spec §8.1–8.8 with evidence pointers to W0–W5 baselines + this milestone.
List deferred items (Tiptap, Word/PDF, payment, etc.).

Do NOT git commit.
Work: c:\Users\99193\Desktop\demo_guo

Report: .superpowers/sdd/w6-task-7-report.md
Return: Status, commits none, test counts, baseline path, concerns
