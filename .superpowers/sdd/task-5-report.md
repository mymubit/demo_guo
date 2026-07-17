# Task 5 Report: 手工验收清单

## Status

**DONE_WITH_CONCERNS** — 自动化侧已验证；真实评测需本机重启 Celery 后由人工完成。

## Automated checks completed

1. **Focused regression suite (22 tests) OK**  
   `test_judge_prompt_injection` + `test_quality_report_substance` + `test_job_llm_logs_access` + `QualityReportNormalizeTests`

2. **Injection markers (via Task 1/4 tests)**  
   - `## 评分细则（内联）` / 权重 / `十维权重摘要` / `S级一票否决`  
   - quality skeleton keys: `evidence` / `deductions` / `dimensions`  
   - compliance sections: 九维 / 三阶段 / P2  

3. **Process check**  
   当前终端未见活跃 Celery worker。**未重启 worker 前，页面评测仍可能跑旧代码。**

## Human checklist (must do before claiming production fix)

```text
1. 停掉旧 Celery → 在 backend 启动:
   py -3 -m celery -A config worker -l info
2. 确保 runserver / 前端使用当前工作区
3. /tools/script-review 上传样本 → 打开评审记录
验收:
  [ ] 调用日志 ≥2 条，可展开 system/user/response
  [ ] 质量报告每维有证据；偷懒则任务失败而非空壳成功
  [ ] 无「总分高 + 重大返工 + 可放行」
  [ ] 合规阻断有中文标题
4. 在评分官 system 中确认:
  [ ] ## 评分细则（内联）
  [ ] 叙事效率 / weight=
  [ ] 十维权重摘要
```

## Concerns

- 旧评审记录不会自动变好，需重新评测。
- Task 5 无法在无 LLM/Celery 的 agent 环境内完成端到端验收。

## Final review fixes (2026-07-17)

- **Judge skeleton regression**: `test_scorer_prompt_includes_quality_report_skeleton_keys` 断言 `最小合法示例`、`dimensions.format` 路径行及 JSON 示例内 `"format"`/`"evidence"`，确保 `render_contract_block` 未被移除。
- **Substance gate wiring**: 新增 `test_substance_gates_wiring.py`，经 `_parse_normalize_validate` 验证 quality_report 空壳（mock schema 通过后）与 compliance_report 薄报告均抛出 `SCHEMA_VALIDATION_FAILED` 及对应门禁文案。
- **Regression**: 24 tests OK（含上述新增用例）。
