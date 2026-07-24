# ScriptForge V3 W4 质检 + 交付 — 终审报告

> **审查范围：** 未提交工作树（read-only，未 mutate git）  
> **计划：** `docs/superpowers/plans/2026-07-23-drama-website-v3-w4-quality-delivery.md`  
> **验收基线：** `docs/superpowers/baselines/2026-07-23-w4-quality-delivery-acceptance.md`  
> **审查日：** 2026-07-23  
> **审查方式：** 计划/基线对照 + 核心路径代码抽查 + 独立机跑 W4 测试子集

---

## Strengths

1. **闭环语义清晰且与计划一致**  
   - `score_quality` / `check_compliance` / `prepare_delivery` 走 `commit_mode: direct`，成功后直接 committed 并 supersede 旧版。  
   - `revise_from_findings` 保持 candidate，确认仍走既有 `confirm_script_candidate`。  
   - `accept_findings` 正确归入 `SYNC_MUTATION_COMMANDS`，与 `ASYNC_STUB_COMMANDS` 清 stub 一致（`types.py` 仅留 `test_model_provider`）。

2. **报告过期（staleness）实现规范**  
   - `report_meta.py` 提供 attach / strip / read / is_stale 四件套，校验前剥离 `_v3_meta`、落库前合并，符合计划推荐路径。  
   - `executor.py` direct 路径在 validate 后统一 `attach_script_meta`，与正文 version 绑定。  
   - API GET 返回 `quality_is_stale` / `compliance_is_stale`；前端 QualityPage 有过期横幅。

3. **交付门禁（无 LLM）正确且可测**  
   - `delivery_gate.evaluate` 覆盖：缺正文、缺/过期报告、质量 verdict/grade 规则、合规 overall_result、blocking_issues vs accepted findings。  
   - `async_runner.py` 在 `requires_delivery_gate` 时 **先于** `execute_generation` 同步跑门禁；失败直接 `failed` + 中文 blockers，不调 LLM（`test_prepare_delivery_gate_fail_skips_llm` 验证）。  
   - DeliveryPage 用 GET `gate.passed` 禁用「生成交付包」按钮，与后端一致。

4. **finding_key 前后端对齐（任务账本曾标注风险，现已闭合）**  
   - 后端：`delivery_gate._blocking_issue_key` 与 `accept_findings.py` 文档注释一致（finding_key → id → title → `blocking:{index}`）。  
   - 前端：`QualityPage.tsx` 显式注释并对齐 `blockingIssueKey` / `qualityDefectKey`；测试断言 accept 传 `blk-1`、revise 传 `defect:0`。

5. **REST + UI 完整，约束达标**  
   - Quality/Delivery 六条 API 已挂 `urls.py`；前端 `/quality`、`/delivery` 路由 + Overview CTA（`projectLabels.ts`）。  
   - UI 无 operation/recipe ID 泄露（页面测试覆盖）；导出 JSON + Markdown，无 Word/PDF/ECharts 新依赖。  
   - `rg v6_runtime|v6_workbench|v6_control_plane` 于 orchestrator / skills_bridge / tasks_v3 / api/v3：**0 matches**。

6. **测试与类型**  
   - 独立机跑 W4 后端 46 tests：**OK**；前端 24 tests + typecheck：**通过**。  
   - `frontend/src/types/v3/domain.ts` 已补全 `QualityState` / `DeliveryState` / `QualityFinding`，无 stub 占位。

---

## Critical

**无（0）**

未发现阻断交付闭环、数据损坏或违反「gate 先于 LLM / 过期报告不可过门禁 / 禁止 v6_*」的缺陷。

---

## Important

**无（0）**

以下为边界/体验项，已归入 Minor，不阻塞 W5：

| 项 | 说明 | 归类理由 |
|----|------|----------|
| `latest_quality_run` 查询含 `accept_findings`、`revise_from_findings` | 接受/修订后「质量任务」状态行可能被非评分 run 覆盖 | 不影响命令执行与轮询；评分/合规按钮仍有独立 pending 态 |
| 旧 committed package 在报告过期后仍可下载 | gate 阻断新 prepare，但历史 package 仍展示 | 计划未要求 package 随正文过期 supersede |

---

## Minor

1. **OpenAPI paths 未登记**（任务账本已知）  
   `openapi.yaml` 有 `QualityState` / `DeliveryState` schema，但 paths 段无 `/projects/{id}/quality/**`、`/delivery/**`。实现与 TS 类型已对齐，建议 W5 或契约 sweep 补全。

2. **门禁单测缺 compliance-only stale 用例**（任务账本已知）  
   `test_v3_delivery_gate.py` 有 `test_stale_quality_report_blocks`，无对称 `test_stale_compliance_report_blocks`。`delivery_gate` 对双报告共用 `is_report_stale`，且 `test_v3_quality_async` 在 confirm 后验证双报告 stale + prepare 失败，逻辑风险低。

3. **`latest_quality_run` 命令范围偏宽**  
   建议收窄为仅 `score_quality`（一行改动），避免 UI 状态行语义漂移。

4. **`production_package` 也被 attach `_v3_meta`**  
   direct 路径对所有 writes 附加正文溯源 meta；当前无 package 过期门禁，无害，后续若做 package staleness 可复用。

5. **blocking_issue 键 fallback 用 title**  
   同 title 多条 blocking 可能键碰撞；依赖 LLM/ fixture 提供 `finding_key` 即可，极端 edge case。

6. **React Router v7 future flag 测试 stderr**  
   基线已记，不影响功能。

---

## Spec Checklist

| # | W4 验收标准 | 结论 | 证据摘要 |
|---|------------|------|----------|
| 1 | committed 正文可评分/合规；报告 committed；stage→quality | ☑ | `recipe_map` requires_committed；`async_runner._advance_stage_after_success`；`test_v3_quality_async` |
| 2 | 报告带 source_script_version；升版后 is_stale；过期不可过门禁 | ☑ | `report_meta` + `test_v3_report_meta`；`test_stale_quality_report_blocks`；API stale flags |
| 3 | accept_findings + 列表可查 | ☑ | `accept_findings.py` + `test_v3_accept_findings` + API GET findings |
| 4 | revise_from_findings → candidate；confirm 后报告过期 | ☑ | executor candidate 路径；async confirm 后 `is_report_stale` 断言 |
| 5 | 未通过/过期 prepare 失败说明原因；通过→package + stage=delivery | ☑ | `delivery_gate` + gate fail skip LLM + success stage 测试 |
| 6 | UI /quality /delivery；CTA；无 op ID；无新依赖 | ☑ | router + pages + Overview；QualityPage.test 无 recipe id |
| 7 | W0–W3 回归；grep 无 v6 | ☑ | 基线 143 backend OK；本审 W4 46 OK；rg 0 matches |

### Global Constraints

| 约束 | 结论 |
|------|------|
| 无 v6_runtime / v6_workbench / v6_control_plane | ☑ |
| 无 UI operation ID | ☑ |
| mock LLM / 无外网 | ☑ |
| 无新第三方库 | ☑ |
| prepare_delivery gate 先于 LLM | ☑ |
| stale reports block gate | ☑ |

### 独立机跑（本审复核）

```text
Backend W4 suites: 46 tests — OK (37.3s)
Frontend: 24 passed (4 files) + typecheck exit 0
```

---

## Verdict

### Ready for W5?

**Yes**

- **Critical：0**  
- **Important：0**  

W4 质检→接受→修订→门禁→交付闭环已实现，与计划/设计 §8.2–8.3 对齐；已知遗留均为 Minor 且已在基线记账。可在修复 OpenAPI paths / 补 compliance-stale 单测等 Minor 项的同时并行启动 W5 计划。

---

*审查人：Senior Code Reviewer（终审 agent，read-only）*
