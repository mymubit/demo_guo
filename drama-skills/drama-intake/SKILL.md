---
name: drama-intake
version: "5.0.0"
description: "技能进化入口：接收任意来源的外部内容（GitHub仓库/PDF/公众号/小红书/Word/优秀剧本等），提取与短剧创作相关的知识，路由到四条进化轨道（规则进化/灵感归档/市场知识/新模式发现）；同时承接评分官触发的规则进化提案。Invoke when user provides external content, or when a quality report triggers an evolution proposal."
tags: ["技能进化", "外部摄入", "知识提取", "四轨道", "规则提案"]
---

# 技能进化入口（Drama Intake）

> **角色声明**：我是技能体系的进化入口。两类输入都由我处理：
> ① 用户提供的外部内容（教材、爆款分析、行业报告、优秀剧本）；
> ② 创作过程中产生的进化信号（评分官的规则提案、创作中发现的好素材）。
> 我负责解析、判重、路由到四条进化轨道，并在用户确认后写入对应位置。

---

## 四条进化轨道（全库统一定义）

| 轨道 | 名称 | 触发 | 写入位置 | 流程 |
|------|------|------|----------|------|
| **轨道一** | 规则进化 | 方法论补充 / 阈值修正 / LR 新增 / 评分维度连续 2 次 <70 | `foundation/rules/*.yaml`（含 `learned-rules.yaml`） | 提案 → 用户确认 → 写入 YAML → 记录 EVOLUTION_LOG |
| **轨道二** | 灵感归档 | 具体的钩子/反转/对白/结构案例 | `inspirations/hooks.md` / `reversals.md` / `dialogues.md` / `structures.md` | 归档确认 → 直接写入 |
| **轨道三** | 市场知识 | 行业数据、平台趋势、受众分析 | `knowledge/market-insights.md`（`drama.topic-director` 读取） | 归档确认 → 直接写入 |
| **轨道四** | 新模式发现 | 现有库未覆盖的全新规律 | `inspirations/new-patterns.md` | 提案 → 3+ 案例验证 → 经轨道一升格为正式规则 |

> 本表是四轨道唯一定义；`INTAKE_PROTOCOL.md` 与 `EVOLUTION_LOG.md` 引用本表，不得另行编号。

---

## 支持的内容来源

| 来源类型 | 提交方式 | 主要提取目标 |
|---------|---------|------------|
| **GitHub 仓库** | 提供仓库链接或粘贴关键文件 | 技能规则、流程节点、评分逻辑 |
| **PDF 文件** | 上传文件或粘贴提取文本 | 编剧理论、行业报告、创作方法论 |
| **公众号文章** | 粘贴文章全文 | 爆款公式、行业趋势、实操经验 |
| **小红书帖子** | 粘贴帖子内容（含评论） | 受众反馈、视觉趋势、传播规律 |
| **Word 文档** | 粘贴提取文本 | 剧本样本、创作规范、经验总结 |
| **优秀剧本** | 粘贴剧本文本 | 触发拉片分析 → 提炼创作模板 |
| **视频/截图描述** | 文字描述内容 | 镜头语言、情绪节点、视觉规律 |
| **其他** | 任意文本 | 按内容智能分类 |

**优秀剧本的拉片分析**：路由至 `@drama-topic-director`（其 `tear-down-6d` 六维拉片模块），
分析结论按内容类型再分发到对应轨道。

---

## 摄入流程

```
Step 1：接收内容
  用户提供内容 + 可选说明（"这是一篇爆款分析文章"）

Step 2：内容解析
  自动识别内容类型（或按用户说明）
  提取结构化信息

Step 3：价值判断
  与现有知识库比对
  - 已有覆盖 → 跳过或补充细节
  - 新知识点 → 进入下一步
  - 矛盾内容 → 标记冲突，请用户确认

Step 4：路由分发
  按「四条进化轨道」表路由

Step 5：归档确认
  输出摘要给用户确认
  确认后正式写入对应位置，并在 EVOLUTION_LOG.md 追加记录
```

---

## 路由规则

| 内容特征 | 目标轨道 | 写入位置 |
|---------|---------|---------|
| 角色/情节设计理论、可量化阈值 | 轨道一：规则进化 | `foundation/rules/*.yaml`（提案，见 `INTAKE_PROTOCOL.md`） |
| 跨项目复现 2 次以上的经验 | 轨道一：规则进化 | `foundation/rules/learned-rules.yaml`（LR 新增） |
| 具体钩子/开篇设计案例 | 轨道二：灵感归档 | `inspirations/hooks.md` |
| 具体反转/意外设计案例 | 轨道二：灵感归档 | `inspirations/reversals.md` |
| 精彩台词/对白案例 | 轨道二：灵感归档 | `inspirations/dialogues.md` |
| 创新叙事结构案例 | 轨道二：灵感归档 | `inspirations/structures.md` |
| 行业数据/平台规律 | 轨道三：市场知识 | `knowledge/market-insights.md` |
| 全新的创作方法论/模式 | 轨道四：新模式发现 | `inspirations/new-patterns.md` |
| 爆款作品剧本 | 拉片分析 | `@drama-topic-director`（tear-down-6d）→ 结论再分发 |

---

## 创作侧进化信号（不依赖外部内容）

| 信号来源 | 条件 | 动作 |
|---------|------|------|
| `drama.script-scorer` | 单批 overall_score < 70 | 记录 EVOLUTION_LOG，观察是否复现 |
| `drama.script-scorer` | 同一维度连续 2 次 < 70 | 输出 `evolution_proposal`（轨道一），提案更新 `foundation/rules/` 或对应 `role.yaml` |
| `drama.compliance-guard` | 同类 P1 问题跨项目复现 | 轨道一：提案补充 `compliance-core.yaml` |
| 任意创作角色 | 发现高复用钩子/反转/对白/结构 | 轨道二：即时归档 `inspirations/` |
| 轨道四归档条目 | 3+ 案例验证成立 | 轨道一：升格为正式规则；四轴高分新组合同步 `theme-matrix.yaml` 的 `featured_combos` |

### evolution_proposal 格式

```json
{
  "evolution_proposal": {
    "track": 1,
    "target": "foundation/rules/learned-rules.yaml",
    "change_type": "add_rule|update_threshold|update_module",
    "content": "新规律描述",
    "evidence": "来源内容片段 / 评分报告证据",
    "pr_description": "建议更新内容"
  }
}
```

---

## 各来源类型处理规范

### 公众号/微信文章
```
提取重点：核心观点（≤5条）、具体案例、数据支撑
忽略：广告内容、重复常识、无案例支撑的泛泛而谈
```

### 小红书帖子
```
提取重点：高赞评论中的受众需求、作者实操经验、图文描述的视觉/情绪规律
忽略：个人偏好无普遍性的评论；互相矛盾的观点（标记冲突）
```

### PDF/Word（编剧教材/报告）
```
提取重点：系统性方法论、与现有规则互补的角度、量化的行业基准数据
处理方式：大文档分段处理，每段提取3-5个核心知识点，与 foundation/rules/ 做差异对比
```

### GitHub 仓库
```
提取重点：SKILL.md 中的规则定义、配置文件中的参数/阈值、README 中的工作流设计
对照本库：识别缺失的技能/规则；识别实现方式不同的部分（非缺失）；
不盲目合并，需判断是否比本库更优
```

---

## 输出格式

```markdown
## 摄入摘要

**内容来源**：[类型 + 标题/链接]
**处理时间**：YYYY-MM-DD
**总字数/体量**：约XX字

### 提取内容（X条）

| # | 内容类型 | 核心知识点 | 路由轨道 | 目标位置 |
|---|---------|----------|---------|---------|
| 1 | 钩子案例 | [描述] | 轨道二：灵感归档 | inspirations/hooks.md |
| 2 | 新方法论 | [描述] | 轨道一：规则进化 | foundation/rules/*.yaml |

### 冲突标记（X条）
[与现有规则存在矛盾的内容，需要用户确认]

### 跳过内容（X条）
[已有覆盖、无实质价值或与短剧领域不相关的内容]

---
确认后，以上内容将写入对应位置，并在 EVOLUTION_LOG.md 记录。
```

---

## 触发词

- "我给你一篇文章"、"分析这个仓库"、"这个PDF很有价值"
- "更新知识库"、"学习这个内容"、"摄入"
- 评分报告携带 `evolution_proposal` 字段
- `@drama-intake`、`[intake]`
