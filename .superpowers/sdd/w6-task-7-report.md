# W6 Task 7 报告：§8 全量回归基线

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W6 — Spec §8 全量回归基线  
**Commits:** none（用户明确跳过）  
**Brief:** `.superpowers/sdd/w6-task-7-brief.md`  
**Plan:** `docs/superpowers/plans/2026-07-23-drama-website-v3-w6-billing-legacy-cut.md` Task 7

---

## What I Did

1. **后端全量机跑**（`apps.drama.tests`，`sqlite_test`）— 无需因残留 import 修代码或排除模块  
2. **前端** `npm test` + `npm run typecheck`  
3. **grep 守卫**（legacy v6 / v2 studio / GenerationService）— 0 匹配  
4. **创建基线** `docs/superpowers/baselines/2026-07-23-w6-billing-legacy-cut-acceptance.md`（§8.1–8.8 + 延期清单）  
5. **更新 roadmap** `docs/superpowers/plans/2026-07-22-drama-website-v3.md` — W6 ✅；phase-1 complete  
6. **追加** `.superpowers/sdd/progress-w6.md` Task 7 DONE  

---

## Verification

### Backend

```powershell
cd backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests --settings=config.settings.sqlite_test -v 1
```

**结果：** Ran **298** tests in 126.645s — **OK**

### Frontend

```bash
cd frontend
npm test
npm run typecheck
```

**结果：** **154** passed（33 files）；typecheck exit 0

### Grep

```bash
rg "v6_runtime|v6_workbench|v6_control_plane|/api/v2/studio" …
rg "from apps.drama.v2|GenerationService" backend/apps/drama --glob "!migrations/**"
```

**结果：** 0 matches

---

## Deliverables

| 产物 | 路径 |
|------|------|
| 验收基线 | `docs/superpowers/baselines/2026-07-23-w6-billing-legacy-cut-acceptance.md` |
| Roadmap | W6 ✅；phase-1 complete note |
| Progress | Task 7 DONE in `progress-w6.md` |

---

## Return Summary

| 项 | 值 |
|----|-----|
| Status | DONE |
| Commits | none |
| Backend | 298 OK |
| Frontend | 154 passed + typecheck OK |
| Baseline | `docs/superpowers/baselines/2026-07-23-w6-billing-legacy-cut-acceptance.md` |
| Concerns | 见下 |

---

## Concerns

- **非阻塞遗留（已写入基线）：** Tiptap、Word/PDF、真实支付/配额、旧 Django 表未删迁移、`drama-skills/v6/operations` 保留、试连日志未挂 `v3_command_run`、React Router v7 future flag 警告。  
- **无阻塞失败：** 全量套件绿；未发现需热修的残留 import。  
- **未 commit：** 按指令保持工作区未提交状态。
