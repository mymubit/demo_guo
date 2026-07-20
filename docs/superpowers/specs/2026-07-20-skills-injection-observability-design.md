# 技能注入可观测与优化 — 设计规格

> 状态：已批准（对话确认）  
> 日期：2026-07-20  
> 范围：`drama-skills/`、`backend/apps/drama/`（loader / PromptBuilder / LLM 日志）、`frontend` 运维页（LLM Logs / Skills Inventory / SkillOps）  
> 实施路径：先观测后收敛（A → D 最小 UI → B → C → D 增强）

## 1. 背景与决策

角色执行当前是黑盒：`PromptBuilder` 将 SKILL / modules / rules / knowledge / fewshots / anti / 契约拼成巨大 system 字符串；真实 LLM 调用只落全文 + token usage。运维侧已有 Skills Inventory **干跑**分层字数，但与生成路径算法可能漂移，且无 call 级结构化「注了什么」。

痛点：

- 不知道每次调用用了哪些技能/模块/知识
- 不知道条件注入是否生效、是否误跳过
- 不知道哪些层不该全文注入、谁贡献了大 token
- SkillOps（结构化失败）与注入诊断语义混在一起，难以归因

已确认决策：

| 决策点 | 选择 |
|--------|------|
| 范围 | **A+B+C+D 全要**（可观测 + 注入策略 + 内容瘦身 + 诊断闭环） |
| 整体打法 | **方案 1：先观测后收敛**（禁止盲砍内容） |
| Skills SSOT | 仍在 Git `drama-skills/`；不把技能正文搬进 DB |
| 新依赖 | **禁止**引入新第三方库 |
| 行为变更安全 | B/C 可按角色回滚；`max_chars: 0` / flag 作逃生阀 |
| Token 计量 | 层占比用 **chars**；供应商 `prompt_tokens` 作辅助，不做本地 tokenizer |

## 2. 目标与非目标

### 目标

1. 任意一次成功/失败 LLM 调用，能在约 30 秒内回答：注了哪些 module / knowledge / rule section、各层 chars、跳过原因、是否截断。
2. Inventory 干跑与真实调用共用同一套装配逻辑与 `InjectionManifest`，禁止两套算法漂移。
3. 条件注入默认开启；分角色 budget / mode；高负载角色 system 可降，且相关 eval 不掉档。
4. 契约单一真相：modules / knowledge 注入清单 / rule sections 以 `role.yaml` 为准，CI 防漂移。
5. Logs ↔ Inventory ↔ SkillOps 打通：注入视图、告警、失败归因启发式。

### 非目标

- 不自动改写 `role.yaml` / 不自动瘦身文件。
- 不做跨项目成本大盘（可后续）。
- 不把 knowledge 正文再存一份到 DB。
- 首版不做消息推送告警。
- 不改变 LLM 供应商协议与现有「三栏原文完整落库」原则。

## 3. 总体架构与子项目

```
D 运维闭环（Logs / Inventory / SkillOps）
        ▲
A InjectionManifest（每次 LLM 调用落库）
        ▲
B 注入策略（enable_when / 预算 / as_index / knowledge.mode）
C 内容瘦身（exec/ref/doc + SSOT 校验）— 由 A 数据驱动
```

| 代号 | 名称 | 交付物 | 依赖 |
|------|------|--------|------|
| **A** | 注入可观测 | Manifest 类型；装配统一；`DramaLlmCallLog.injection_manifest`；API | 无 |
| **B** | 注入策略 | 全角色 `evaluate_enable_when`；policy 契约；预算接线；可选 flag | A 验证 |
| **C** | 内容优化 | SSOT 校验；Top 文件拆 exec/ref；SKILL 真索引；scorer 输出契约收敛 | A 数据 |
| **D** | 诊断闭环 | 注入 Tab；告警；SkillOps 归因；Inventory 对比真实调用 | A 必选 |

推荐实施顺序：**A → D 最小注入 Tab（可与 B 并行）→ B → C → D 告警/归因增强**。

### 全局约束

- Manifest 与真实 `system_prompt` 可对账：`sum(layers) + 分隔符` 与 `system_chars` 误差 ≤ 64。
- 生成路径行为变更必须可回滚。
- 前端延续现有运维视觉语言，不新造第四个大后台。

### 成功标准（整体）

1. 新调用必有结构化注入清单可查。
2. story-bible / script-writer / delivery 等在 B+C 后 system_chars 相对基线下降，eval 不掉档。
3. 排障路径：打开 log → 注入 Tab →（若失败）SkillOps 跳转同一 log。

---

## 4. A — InjectionManifest 与装配改造

### 4.1 数据契约

```ts
type InjectionManifest = {
  version: 1
  agent_id: string
  bundle_version: string
  built_at: string  // ISO

  layers: {
    skill: LayerStat
    modules: LayerStat
    rules: LayerStat
    knowledge: LayerStat
    fewshots: LayerStat
    anti: LayerStat
    scoring_inline: LayerStat
    contract: LayerStat
    header: LayerStat
  }

  modules: {
    included: ModuleItem[]  // id, label_zh, chars, mode: "full"|"index"|"truncated"
    skipped: ModuleItem[]   // + reason: enable_when|missing|budget|policy
  }
  knowledge: {
    included: FileItem[]    // path, chars, mode
    skipped: FileItem[]     // + reason: platform|genre|budget|missing
  }
  rules: {
    sections_included: string[]
    item_count: number
    truncated: boolean
    max_chars: number       // 0 = 未启用预算
  }
  policies: {
    evaluate_enable_when: boolean
    module_max_chars: number
    rule_max_chars: number
    knowledge_max_chars: number
    module_as_index: boolean
  }

  system_chars: number
  user_chars: number
  checksum: string          // sha256(system)[:16]
}

type LayerStat = { chars: number; truncated: boolean }
```

条目只存元数据，不存正文（正文仍在 `system_prompt`）。

### 4.2 装配改造

1. `PromptBuilder.build` 返回 `(system, user, manifest)`。
2. Loader 新增 `assemble_modules_for_role` / `assemble_knowledge_for_role` / `assemble_rules_for_role`（或等价），产出 `text + included/skipped`；保留现有返回 `str` 的方法作薄封装以兼容。
3. `PromptBuilder` 与 `build_prompt_breakdown` **只走 assemble\***，禁止手算第二套 included。
4. 先结构化再 `join`；禁止从最终字符串反推清单。

### 4.3 落库与传递

| 点 | 改动 |
|----|------|
| `DramaLlmCallLog` | `injection_manifest = JSONField(null=True, blank=True)` |
| `llm_call_context` | 可选携带 manifest；`GenerationService` 在 `build()` 后写入 |
| `LlmCallLogService.record` | 从 context 或显式参数写入；连通测试可为空 |
| 详情 API | 返回完整 manifest；列表可只返回摘要字段以免膨胀 |

失败调用：只要 `build` 成功即落 manifest。

### 4.4 A 不做

不改默认注入策略；不拆 knowledge 文件；不做告警 UI。

### 4.5 A 验收

- 生成一次任意生产角色，日志详情可见完整 manifest。
- 同 settings 下 dry-run breakdown 与真实调用的 layers / modules 集合一致。
- 8 角色 build 对账测试通过；旧日志 `null` 可降级展示。

---

## 5. B — 注入策略收敛

### 5.1 原则

1. 先条件、再预算、最后截断。
2. 预算是护栏不是质量策略；真正减负靠 C。
3. 按角色分级，禁止全局一刀切 `max_chars`。
4. 可回滚：角色级 `max_chars: 0`；可选 `SKILLS_INJECTION_POLICY_ENFORCED`（关则忽略预算，行为≈今日）。

### 5.2 条件注入

- 全角色补 `module_policy.evaluate_enable_when: true`（无 modules 的角色无行为变化）。
- catalog 已有条件保持：`tear-down-6d`、`adaptation-originality`、delivery 扩展包。
- 新增 catalog 条件可后续迭代（如 payment / production-feasibility），非 B 阻断项。

### 5.3 Policy 契约（role.yaml）

```yaml
module_policy:
  evaluate_enable_when: true
  as_index: false
  max_chars: 0

rule_policy:
  scopes: [...]
  sections: [...]
  max_chars: 0

knowledge_policy:
  mode: full               # full | sections | index
  max_chars: 0
  # mode=sections 时：
  # sections: [...]        # 对齐 knowledge-sections 锚点；抽不到则 fallback full 并标 fallback
```

- `as_index` 必须接到 `PromptBuilder`（loader 已有参数，当前未用）。
- `knowledge_policy.mode` 为新能力；`max_chars` 钩子已存在。

### 5.4 分角色首版基线

先全开 evaluate；**仅**给高负载角色加 knowledge 预算，其余用 A 跑一周再定：

| 角色 | 首版动作 |
|------|----------|
| topic-director | evaluate 已开；knowledge 建议 `max_chars: 6000` 或 sections |
| story-bible | knowledge：`mode=sections` 或 `max_chars: 8000` |
| delivery-tool | 长文 knowledge 改 sections/index |
| episode / writer / scorer / revision / compliance | 开 evaluate；预算观望 |

`as_index` 默认 false；仅当 modules 层长期过大且 eval 证明后才开。

### 5.5 B 验收

- 无 `reference_dramas` → `tear-down-6d` 在 skipped。
- `entry_type=original` → `adaptation-originality` skipped。
- deliverables 不含 storyboard → `storyboard-9col` skipped。
- 开启 knowledge 预算后 manifest 可见 truncated，且抽样 eval / schema 仍可通过。

---

## 6. C — 内容瘦身与双 SSOT 治理

### 6.1 数据驱动

C 每一刀附：改前/改后 manifest 快照 + 对应 eval。禁止无 A 数据盲砍。

建议门槛：单 knowledge >4k chars、单 module >3k、某角色 rules 层 >8k → 进入改造队列。

### 6.2 SSOT 规则

| 概念 | 唯一正式来源 | 校验 |
|------|--------------|------|
| 模块注入清单 | `role.yaml.modules` | SKILL frontmatter `modules`、`registry.yaml` 摘要必须一致 |
| Knowledge 注入清单 | `role.yaml.knowledge_policy`（paths/includes） | SKILL references 中 knowledge 路径由脚本同步为文档索引 |
| Rule sections | `role.yaml.rule_policy.sections` | `knowledge-sections.md` 角色表由 role 生成或 CI 对比 fail |
| 文档-only refs | modules/rules 路径等 | Inventory 分栏「注入中 / 仅文档索引」；不得标为将注入 |

`build/validate_skills.py`（或等价）纳入上述断言；catalog `target_roles` mismatch 分阶段升为 CI error。

### 6.3 文件形态

| 形态 | 用途 | 注入 |
|------|------|------|
| exec | 步骤/硬约束/检查清单 | 默认可全文 |
| ref | 长方法论/案例 | 默认 index/sections |
| doc | 人读文档 | **永不**进 prompt |

优先改造（以 A 数据校准）：`shanyin-*.md`、delivery 导演长文、明确非运行时的 system/output-schemas 类文档。

SKILL.md：真索引体，建议正文硬顶（由 `slim_skill_bodies` / CI warn|fail）。

Scorer：收敛 SKILL 对超长 `evidence` / `verdict_detail` 的字数要求，降低 completion tokens。

### 6.4 与 B 配合

理想态：生产很少 `truncated=true`；预算仅防回归炸窗。C 完成后可下调过严 `max_chars`。

### 6.5 C 验收

- validate 零漂移。
- Inventory 可区分注入 vs 文档-only。
- 目标角色 system_chars 下降且 eval 不掉档；scorer completion 中位数下降（抽样人工确认可解释性）。

---

## 7. D — 端到端诊断闭环

### 7.1 三页分工

| 页面 | 增强 |
|------|------|
| LLM Logs `CallDetailDrawer` | Tab「注入」：分层占比、included/skipped、policies、截断标记 |
| Skills Inventory | 干跑 vs 最近真实调用对比；mismatch / 常 truncated 待办只读列表 |
| SkillOps | 失败项挂 `llm_log_id` + injection_summary + suspected_causes；跳转 Logs 注入 Tab |

工作台 `JobLlmCallLogs*` 复用同一注入面板；列表小标签：正常 / 有截断 / 过大。

### 7.2 告警（读详情时计算 `injection_alerts`）

可配置阈值（ops 配置或 settings 常量）：

| 规则 ID | 条件 | 级别 |
|---------|------|------|
| `system_chars_high` | 超角色绝对上限或基线×1.5 | warn |
| `layer_dominant` | 单层 / system > 0.45 | warn |
| `budget_truncated` | 任一层 truncated | warn |
| `enable_skipped_core` | core 模块 skip 且任务失败 | info |
| `token_prompt_high` | 有足够样本后超 P95（可二期） | warn |

首版不做推送。

### 7.3 失败归因启发式

```ts
suspected_causes?: Array<
  | "schema_contract"
  | "over_injection"
  | "missing_module"
  | "model_error"
  | "unknown"
>
```

- HTTP/空响应 → `model_error`
- JSON/schema 失败 + truncated → `over_injection` + `schema_contract`
- JSON/schema 失败、无截断 → `schema_contract`（继续回流 anti-examples）
- 失败且 core 模块 skipped → `missing_module`

`over_injection` **不**导出 anti-examples，引导改 B/C。

### 7.4 D 不做

自动改 YAML；成本大盘；正文二次落库。

### 7.5 D 验收

- 新调用注入 Tab 与同 settings 干跑一致。
- 人为截断可见告警。
- SkillOps schema 失败可跳到对应 log 注入视图。
- 旧 log `null` 无回归。

---

## 8. 风险与回滚

| 风险 | 缓解 |
|------|------|
| B 预算过紧导致质量下降 | 分角色灰度；flag 关闭预算；eval 门禁 |
| Manifest 与 system 不对账 | 对账单测；禁止反推清单 |
| C 拆文件丢硬约束 | exec/ref 分离评审；eval + 人工抽检 |
| 列表 API 膨胀 | 列表只返回摘要；详情才全量 manifest |
| 双写 SSOT 一时不一致 | CI fail；知识 paths 以 role.yaml 为写入源 |

---

## 9. 测试策略

- **A**：manifest 结构；8 角色对账；breakdown ≡ build manifest；record 落库字段。
- **B**：enable_when 真假矩阵；预算截断标记；flag 开关行为。
- **C**：validate_skills 漂移用例；标 doc 的路径永不出现在 knowledge.included。
- **D**：详情序列化含 manifest/alerts；SkillOps 关联字段；前端类型与 Tab 冒烟（对齐现有 ops tokens 测试风格）。

普通逻辑 ≥5 case；装配/对账/enable_when 等高风险 ≥10–12 case。

---

## 10. 文档与后续

- 实现计划：待本 spec 审阅通过后，由 `writing-plans` 写入 `docs/superpowers/plans/2026-07-20-skills-injection-observability.md`（若过大可拆 A/B 与 C/D 两份 plan）。
- 不在本 spec 范围改用户产品文档，除非 API 字段对外暴露需同步契约说明。
