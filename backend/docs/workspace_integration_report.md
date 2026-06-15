# 全量业务联调报告

**日期**：2026-06-13  
**项目**：`ce9822f4-2606-447e-bd4c-92b3ea075c61`（10 集 · sweet-pet · 工作台）  
**模式**：真实 LLM + 同步 Worker（`run_workspace_live_chain` 管理命令）

---

## 一、自动化基线

| 指标 | 结果 |
|------|------|
| `apps.creation.tests` + `apps.portal.tests` | **104** 项全部通过 |
| 新增用例 | workspace_service / editor_save / post_script / script_export / polish_apply / portal workspace API |
| 基线对比 | 80 → **104**（+24） |

---

## 二、五步主链（真实 LLM）

| 节点 | 状态 | 耗时 | 关键断言 |
|------|------|------|----------|
| 1 立项 | 通过（创建时写入） | — | `project_brief` 有 `coreHook` |
| 2 结构 | **通过** | ~420s | `sixStagePlan`=6、`keyReversalPoints`=8；`world-validator` CLI failed 但轨迹诚实 |
| 3 人设 | **通过** | ~181s | `characterCount`=4；`relationship-weaver` 执行 |
| 4 大纲 | **通过** | ~541s | framework + fill_all；`episodes` 部分生成（4/10 集纲后 fill）；`plan-fixer` LLM JSON 解析失败但节点完成 |
| 5 剧本 | **通过**（重试后） | 批次1 + 批次2（重试） | 10 集全量；gate 执行；第二批次首次空 `episodes`，加重试后成功 |

**轨迹**：各节点 `execution_trace` 含 executed / failed / skipped，非全绿假轨迹。

### 后处理链（剧本全量后）

| 项 | 结果 |
|----|------|
| `run_agent_post_chain` | **通过** |
| `project.status` | `completed` |
| `post_script.status` | `done` |
| `can_share` | `true` |
| 分享 API | `share_ok: true` |
| 综合评分 | 52（`review_passed: false`） |

---

## 四、已修复前后端不一致

| 优先级 | 问题 | 修复 |
|--------|------|------|
| P0 | 分享与 `status` 冲突 | 后处理成功 → `completed`；`build_workspace_payload` 增 `can_share`；前端分享按钮改 `can_share` |
| P1 | Brief `themeDisplayName`/`episodeCount` 未持久化 | `apply_editor_save` node 1 写回 |
| P1 | 人设 legacy `name`/`oneLineSummary` | `_patch_char` 补齐字段 |
| P2 | 作品列表 `pending`→`draft` | `normalizeWorkItem` 按 `pipeline_mode`+进度区分 |
| P2 | `post_script.chain` 硬编码 | 从 `post_script_chain()` + marketing 动态组装 |
| 额外 | 循环导入阻塞 migrate | `agents/__init__.py` 懒加载；insight/review 延迟 import |
| 额外 | LLM max_tokens 未配置阻断联调 | `resolve_agent_max_tokens` 回退 `FUSION_LLM_MAX_TOKENS` |
| 额外 | 剧本批次 LLM 空响应 | `script_engine` 单批次重试一次 |

---

## 五、存量补全

```bash
python manage.py backfill_artifact_enrichment --dry-run --project-id ce9822f4-2606-447e-bd4c-92b3ea075c61
# → DRY 1 条，不消耗 LLM
```

---

## 六、风险与后续

1. **子技能 CLI**：`sub-world` / `sub-plan` 校验常 failed，fixer 后仍可能 warning——符合「诚实轨迹」设计。
2. **大纲 fill_all**：LLM 可能未一次写满 10 集纲，需多轮 `next`/`block`（联调命令已封装 framework+fill_all）。
3. **剧本第二批次**：依赖 LLM 稳定性；已加重试，建议生产侧监控空 `episodes` 率。
4. **Windows 控制台**：GBK 日志编码偶发 `UnicodeEncodeError`（不影响业务 JSON 输出）。

---

## 七、复现命令

```bash
cd ScriptForge/backend
python manage.py test apps.creation.tests apps.portal.tests -v 1
python manage.py run_workspace_live_chain --episodes 10 --nodes 2,3,4,5
# 续跑已有项目
python manage.py run_workspace_live_chain --project-id <uuid> --nodes 5
```
