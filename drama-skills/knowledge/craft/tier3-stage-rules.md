# stage_playbook 参考（按角色阶段）

> **参考长文**；可执行规则 SSOT：`foundation/rules/stage-playbook.yaml`
>
> 下文按 `drama.*` 角色组织。运行时以 `role.yaml` 的 `rule_policy` 与 `input_contract` 为准。

---

## drama.topic-director — 选题定调（原创通道入口）

### 标准输出

```
故事梗概 + 市场机会 + 爆款因子 + 竞品避雷 + 差异化策略
首集钩子方向 + 首付费卡点方向 + 合规初筛（数值见 `foundation/constraints/commercial-formulas.yaml`）
```

### 输入 / 输出

- 输入：主题 / 故事梗概 / 题材矩阵 / 参考剧
- 输出 schema：`project_brief` v1

---

## drama.story-bible — 剧本蓝图（人物层 + 结构层）

### 双模式

```
原创模式：输入 project_brief，展开梗概/人物/结构
改编模式：输入 params.external_story，先提取再补全，
          显式输出「保留/强化/改写」说明 + 原创性风险自检
两种模式输出同一 `story_bible` schema v1
```

### 角色密度（人物层）

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

### 轻量世界规则

```
只保留会影响人物行动、关系冲突和剧情选择的世界规则。
普通都市/家庭/职场短剧不得输出冗长世界观文档。
```

### 六阶段集数分配（结构层，100 集基准，等比缩放）

```
阶段 1 开篇 10%  情绪 3→6
阶段 2 升温 20%  情绪 5→7
阶段 3 高潮 20%  情绪 7→9
阶段 4 转折 20%  情绪 8→10
阶段 5 冲刺 15%  情绪 9→10
阶段 6 结局 15%  情绪 10→余韵
```

题材配比由 `foundation/theme-matrix.yaml` 合成 `rule_params.act_ratio`，统一经 `genres/matrix.yaml` 注入。

### 结构层输出

```
1. 全剧主线
2. 六阶段结构
3. 主线 / 支线安排
4. 人物弧光落点
5. 关键反转位置
6. 付费节点分布
7. 伏笔总表
8. 全剧情绪曲线
```

### 全剧检验

```
每 5 集 ≥1 次 A 级反转；阶段 4 情绪谷底 ≤2；终局 3 集加速。
剧本蓝图官不展开逐集细节。
```

---

## drama.episode-designer — 分集设计

### 单集设计卡（输出 `narrative_plan`）

```
1. 本集标题
2. 核心事件（≤20 字）
3. Goal × Conflict
4. 情绪强度（1–10）
5. 集首钩子
6. 集末钩子
7. 爽点与反转
8. 付费卡点
9. 伏笔埋设 / 回扣
10. 双轨节奏
```

### 单集检验

```
集末有明确钩子；禁止连续 2 集纯铺垫（峰值 <6）。
分集设计官不得重写 story_bible 的主线和六阶段结构。
```

---

## drama.script-writer — 剧本正文

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

## drama.script-scorer — 十维评分（质检环 · 独立技能）

```
1. 评分对象统一读取 `latest_script`
2. 输出 quality_report（schema v1）
3. defects 路由至 drama.revision-master；低于 B 级（75）阻断下一批生成
4. overall_score < 70 → 记录至 EVOLUTION_LOG，考虑规则补丁
5. 某维度连续 2 次 < 70 → 经 @drama-intake 轨道 A 提案更新 foundation/rules/
```

评分维度 SSOT：`foundation/constraints/quality-scoring.yaml`

---

## drama.revision-master — 剧本修复（质检环 · 独立技能）

### 修复边界

```
只能根据评分报告、合规报告或用户指定问题修复文本执行质量。
不得推翻已确认的选题、故事蓝图和分集设计。
输出后必须交回 drama.script-scorer 复评。
```

输出：`polished_script`（schema v1）

---

## drama.compliance-guard — 合规（质检环 · 独立技能）

```
与评分官并行触发；审查对象统一读取 `latest_script`。
P0 或未解决 P1 → 拒绝出具通过报告，阻断下游。
详见 knowledge/quality/tier4-compliance.md。
```

输出：`compliance_report`（schema v1）

---

## drama.delivery-tool — 宣发交付（可选工具）

```
前置门禁：必须读取 quality_report + compliance_report；
无合规通过结论或评分低于 B 级（75）时只输出「不可交付+缺口清单」。
```

输出：`production_package`（schema v1）
