# stage_playbook 参考（按角色阶段）

> **参考长文**；可执行规则 SSOT：`foundation/rules/stage-playbook.yaml`
>
> 下文按 `drama.*` 角色组织。运行时以 `role.yaml` 的 `rule_policy` 与 `input_contract` 为准。

---

## drama.world-architect — 世界观设定

### 世界观四块（输出 `world_setting`）

```
settingSummary  → 世界背景摘要（50 字以内）
rootRules       → 核心规则（≤3 条）
coreNouns       → 核心名词定义（题材专有词汇）
dreamIndicators → 梦境三指标预设（安全/满足/现实）
```

### 输入 / 输出

- 必填：`project_brief`
- 输出 schema：`world-setting.v1`

---

## drama.character-designer — 人设开发

### 角色密度

```
主角：1–2 人（完整弧光）
核心配角：2–4 人（各有独立动机）
功能型配角：按需（每人 1 个识别特征）
关系角色上限：≤6 人
```

### 人物弧光硬约束

```
起点（第 1 集）→ 转折 1（≈30%）→ 转折 2（≈70%）→ 终态

禁止：无触发突变；反派无铺垫洗白；弧光与主题无关
```

---

## drama.plot-architect — 结构与分集大纲

### 六阶段集数分配（100 集基准，等比缩放）

```
阶段 1 开篇 10%  情绪 3→6
阶段 2 升温 20%  情绪 5→7
阶段 3 高潮 20%  情绪 7→9
阶段 4 转折 20%  情绪 8→10
阶段 5 冲刺 15%  情绪 9→10
阶段 6 结局 15%  情绪 10→余韵
```

题材配比 override 见 `foundation/rules/genres/*.yaml`。

### 单集大纲六要素（输出 `series_outline`）

```
1. 本集标题
2. 核心事件（≤20 字）
3. 情绪强度（1–10）
4. 钩子类型与描述
5. 结尾悬念（下集钩子）
6. 出场角色（2–5 人）
```

### 全剧 / 单集检验

```
全剧：每 5 集 ≥1 次 A 级反转；阶段 4 情绪谷底 ≤2；终局 3 集加速
单集：集末有明确钩子；禁止连续 2 集纯铺垫（峰值 <6）
```

---

## drama.script-writer — 分集剧本

细则 SSOT：`roles/drama-script-writer/tasks/write-episodes.md` + `foundation/constraints/script-format.yaml`

### 硬规则

```
必须指定 episode_range；单次 ≤5 集
逐集依赖：上一集全文 + memory_checkpoint + 本集大纲条目（LR-008）
每集 1–3 场景；Gate 通过后再写下一集
```

### Gate 检测（每集完成后）

```
□ 场景头格式正确
□ 情绪高点达目标强度
□ 集末悬念钩子
□ 无漏空段落
□ 无 AI 腔
□ 字数在 script-format 范围内
```

---

## drama.script-reviewer — 质量审查

### 审查顺序

```
1. 格式合规
2. 结构（六阶段 + 单集四段式）
3. 人物逻辑
4. 情绪曲线
5. 横截面 / McKee 价值转变
```

输出：`review_report`（schema: `review-report.v1`）

---

## drama.quality-reporter — 质量评分

```
1. 输出 quality_report（schema: quality-report.v1）
2. defects 路由至 drama.polish-master（可选）
3. overall_score < 70 → 记录至 EVOLUTION_LOG，考虑规则补丁
4. 某维度连续 2 次 < 70 → 提案更新 foundation/rules/
```

评分维度 SSOT：`foundation/rules/scoring-core.yaml` + `knowledge/scoring-presets.md`

---

## drama.compliance-guard — 合规（见 tier4-compliance.md）

输出：`compliance_report`（schema: `compliance-report.v1`）
