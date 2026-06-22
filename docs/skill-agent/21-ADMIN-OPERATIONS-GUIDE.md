# Admin 运营操作指南

---

## 1. 目标

运营/编辑在不发版情况下迭代 Skill/Agent 配置的标准路径。

## 2. 角色与入口

| 角色 | 入口 |
|------|------|
| 运营 | React Admin `/admin` |
| 技术 | Django Admin + Console API |

## 3. 常见操作

### 3.1 修改题材参数

1. Admin → 技能 → 题材模板 `ThemeTemplate`
2. 编辑 `params` 或（原子化后）子表 ActRatio / EmotionCurve
3. 保存后清缓存（若有 Redis theme cache）
4. 验证：C 端创作表单题材描述更新

### 3.2 单条规则启停

1. Admin → Tier 规则 → `SkillRulesPanel`
2. 筛选 tier/section/status
3. 编辑 Item `body` 或 archive 单条
4. **禁止**编辑整包 5000 字 JSON

审批 draft → active：`SkillRuleItemApproveView`

### 3.3 钩子/对话模板

1. `HookLibrary` / `DialogueTemplate` 列表
2. 新增一行 content；设 `theme` FK（可选）
3. `is_active=false` 即下线，无需删行

### 3.4 Agent Prompt 发版

1. Agent Hub → 选择 `AgentDefinition`
2. 新建 `AgentPromptVersion`，编辑 system/user 模板
3. 设 `is_active=true`（自动取消同 Agent 其他 active）
4. 填写 `change_notes`
5. 跑 `estimate` 确认 token 未超限

### 3.5 Knowledge 绑定

1. 创建 `AgentKnowledgeItem`（category=rule/knowledge/checklist）
2. `AgentKnowledgeBinding`：order_index, inject_position, max_chars
3. 调整 `AgentDefinition.knowledge_injection_policy` _caps

### 3.6 创作表单 Catalog（原子表）

1. Django Admin → 创作平台 / 预算档位 / 创作入口 等 7 张 `skill_creation_*` 表
2. 或通过 `CreationFormOverrideConfig` 执行 action：**原子表 → JSON 缓存** / **JSON → 原子子表**
3. 保存任意原子行后自动 `sync_overrides_cache` + 清 SSOT catalog 缓存

### 3.7 审查评分预设

1. Django Admin → `ReviewScoringPreset`（含维度/等级 Inline）
2. Action **设为默认预设** — 运行时 `ReviewScoringService.resolve()` 优先读 active preset
3. Legacy `ReviewScoringConfig` JSON 仍作兜底

## 4. evolve_audit 流程（PDF 第六节）

```
低分项目分析 → 自动生成 SkillRuleItem draft
  → 运营 review body/title
  → approve → active
  → 旧 active 同 rule_key archived
```

触发字段：`trigger_project_ids`, `trigger_score_avg`（Config 包级，可选同步到 Item.note）

## 5. Inline 编辑规范（PDF #19）

Django Admin `SkillRuleConfigAdmin`：

- TabularInline：`SkillRuleItem` — fields: title, body, status, sort_order, apply_count
- readonly: apply_count, last_applied_at
- 禁止在 Config 页直接改大 JSON content（只读或 hidden）

## 6. 典型迭代 SOP

| 步骤 | 动作 |
|------|------|
| 1 | 运营改 Theme.params 某题材 act_ratio |
| 2 | 编辑发现剧本质量降 → 登记 `SkillDefect` P1 |
| 3 | 数据组 evolve → 生成 rule Item draft |
| 4 | 负责人 approve Item |
| 5 | 观察 apply_count / 项目评分 |

## 7. 测试矩阵（运营验收）

| 场景 | 检查 |
|------|------|
| 规则上线 | 新 run system prompt 含 `[rule_key]` 块 |
| 规则下线 | archive 后下次 run 不出现 |
| Prompt 切换 | run 记录 prompt_version 新版本 |
| 越权 | 非 staff 无 Admin 写权限 |

## 8. 旧逻辑删除

不再维护：

- Fusion Admin 节点顺序配置
- main-chain orchestration 面板

参考：[21 同目录其他 doc](./20-MIGRATION-RUNBOOK.md)、[22-VERSION-GRAY-RELEASE.md](./22-VERSION-GRAY-RELEASE.md)。
