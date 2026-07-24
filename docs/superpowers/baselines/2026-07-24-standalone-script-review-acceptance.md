# 独立剧本评审验收基线（2026-07-24）

> Spec: `docs/superpowers/specs/2026-07-24-standalone-script-review-design.md`  
> Plan: `docs/superpowers/plans/2026-07-24-standalone-script-review.md`

## 机跑结果

| 项 | 命令 / 说明 | 结果 |
|----|-------------|------|
| 迁移 | `migrate drama 0027_script_review` | 通过 |
| 模型测 | `test_v3_script_review_models` | 5/5 通过 |
| CRUD API | `test_v3_script_review_api` | 6/6 通过 |
| 异步评分/对比 | `test_v3_script_review_async` | 7/7 通过 |
| 前端 vitest | `ScriptReviewsPage.test.tsx` | 3/3 通过 |

合计后端：**18** 用例通过（含 wrap helper）。

## 验收对照

1. [x] 粘贴 / 上传 `.txt|.md` 可创建评审件（非法扩展名 400）
2. [x] 质量评分 / 合规审查异步成功，结果写入 `ScriptReviewRun.report_payload`
3. [x] **不**写入项目 `quality_report` / `compliance_report` artifact；项目 stage 不变
4. [x] 同 `kind` 两条成功记录可 `compare`；不同 kind / 失败态 400
5. [x] 全局导航 `/reviews`；质检页「用外界剧本评分」→ `/reviews/new?project_id=`
6. [x] 仅 owner 可见；他人详情 404

## 手动冒烟（可选）

- 打开「剧本评审」→ 新建粘贴 → 质量评分 → 再评一次 → 勾选两条对比
- 从项目质检页点「用外界剧本评分」，确认 project_id 预填
