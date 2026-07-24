# V3 Phase-3 Roadmap：编辑 / 导出 / 定位 / 回滚 / 预警

> **For agentic workers:** 交错里程碑；**连续执行不停顿向人确认**。REQUIRED: `superpowers:subagent-driven-development`。

**Spec:** `docs/superpowers/specs/2026-07-23-drama-website-v3-phase3-editor-export-rollback-design.md`

## Global Constraints

- 无支付 / 配额
- 禁止 v2/v6_runtime 加功能；UI 无 operation ID
- 新依赖仅：Tiptap 系、`python-docx`（plan 钉版本）
- Commit 默认跳过
- 工作目录：`c:\Users\99193\Desktop\demo_guo`
- 执行中不要向用户询问「是否继续」

## Milestone Index

| 里程碑 | Plan | 状态 |
|--------|------|------|
| **P3-W1** Tiptap + 质检定位 | `2026-07-23-drama-website-v3-p3-w1-tiptap-jump.md` | ✅ 基线 `…-p3-w1-tiptap-jump-acceptance.md` |
| **P3-W2** 后端 docx 导出 | `2026-07-23-drama-website-v3-p3-w2-docx-export.md` | ✅ 基线 `…-p3-w2-docx-export-acceptance.md` |
| **P3-W3** 版本回滚 | `2026-07-23-drama-website-v3-p3-w3-artifact-rollback.md` | ✅ 基线 `…-p3-w3-artifact-rollback-acceptance.md` |
| **P3-W4** 费用预警 + 全量回归 | `2026-07-23-drama-website-v3-p3-w4-cost-alert.md` | ✅ 基线 `…-p3-w4-cost-alert-acceptance.md` |

**Phase-3 complete.**
