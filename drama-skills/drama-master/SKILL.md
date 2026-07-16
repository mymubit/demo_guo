---
name: drama-master
version: "5.0.0"
description: "AI短剧创作总入口 v5.0。4个主链生产角色 + 3个质检环独立技能 + 1个可选交付工具。双通道：原创创作（original-track）与故事改编（story-adapt-track）。Invoke for full drama workflow or stage routing."
tags: ["总入口", "创作", "路由", "双通道", "质检环"]
platforms: [cursor, codex, trae]
input_schema:
  - name: request
    type: string
    required: true
    description: "用户需求描述"
output_schema:
  - name: plan
    type: object
    description: "创作计划（角色分工+执行顺序）"
---

# Drama Master — 创作总入口 v5.0

> **4 主链生产角色 · 3 质检环独立技能 · 1 可选交付工具 · Git SSOT**
>
> 流程 SSOT：`orchestration/original-track.yaml` / `story-adapt-track.yaml`  
> 角色 SSOT：`registry.yaml` + `roles/*/role.yaml`
> 工作台设置：`workbench/workbench.yaml`

---

## 启动方式

```
@drama-master 我要创作一部30集复仇短剧
@drama-master 我有一个故事，帮我改编成短剧    ← 自动进入故事改编通道
@drama-master 从四轴矩阵推荐一个有爆款潜力的题材
@drama-master --stage=writing 从第6集开始继续写剧本
@drama-master [help] 查看角色列表和使用说明
```

---

## 启动问卷

```
① 起点（决定通道）：
   A. 从零开始 / 只有一个想法        → 原创创作通道（先走选题定调官）
   B. 已有故事 / 小说 / 大纲         → 故事改编通道（直接进剧本蓝图官改编模式）
② 题材（原创通道）：受众频道+四轴矩阵（见 `foundation/theme-matrix.yaml`）或一句话创意
③ 集数规模：正整数；工作台可提供常用区间快捷选择
④ 目标平台：读取 `foundation/constraints/platform-profiles.yaml`
⑤ 是否需要宣发交付包（可选工具）
```

---

## 双通道

### 原创创作通道（`orchestration/original-track.yaml`）

```
选题定调官 → 剧本蓝图官 → 分集设计官 → 剧本正文官（分批）
                                        ↓ 每批完成
                            ┌── 质检环（独立技能）──┐
                            │ 评分官 + 合规官（并行）│
                            │   ↓ 未达质量门禁/P1    │
                            │ 修复官 → 复评         │
                            └──────────────────────┘
```

### 故事改编通道（`orchestration/story-adapt-track.yaml`）

```
用户故事(external_story) → 剧本蓝图官（改编模式：提取→补全→原创性自检）
  → 分集设计官 → 剧本正文官（分批）→ 质检环（同上）
```

两通道在 `story_bible` 处汇合，下游完全一致。宣发交付工具在任一通道定稿后可选调用。

---

## 阶段路由

| 阶段 | 角色 | 输出 | 说明 |
|------|------|------|------|
| 选题定调 | topic-director | project_brief | 仅原创通道 |
| 剧本蓝图 | story-bible | story_bible | 梗概+人物+世界观+全剧结构；改编模式吃 external_story |
| 分集设计 | episode-designer | narrative_plan | 分批（episode_range） |
| 正文创作 | script-writer | episode_scripts | 分批（每批 ≤5 集） |
| 独立评分 | script-scorer | quality_report | 质检环；读取 latest_script |
| 合规审查 | compliance-guard | compliance_report | 质检环；与评分并行 |
| 剧本修复 | revision-master | polished_script | 质检环；修复后必须复评 |
| 宣发交付 | delivery-tool（可选） | production_package | 前置门禁：评分+合规通过 |

---

## 直接调用

```
@drama-topic-director       @drama-story-bible
@drama-episode-designer     @drama-script-writer
@drama-script-scorer        @drama-compliance-guard
@drama-revision-master      @drama-delivery-tool
```

---

## 长剧策略

1. story-bible 一次出故事蓝图（50 集以上可分两批：先梗概+人物，再结构层）
2. episode-designer 分批输出分集设计
3. script-writer 每批上限读取工作台 `batch_episode_max`
4. 每批：script-scorer 十维评分 + compliance-guard 合规（并行）；
   未达到当前质量门禁或有 P1 必修项 → revision-master 修复 → 复评通过后再续写

---

## 技能进化闭环

创作与摄入产生的进化信号统一交给 `@drama-intake`（四轨道定义见 `drama-intake/SKILL.md`）：

- 评分官某维度连续 2 次 <70 → 轨道一：规则进化提案
- 创作中发现好钩子/反转/对白/结构 → 轨道二：灵感归档
- 用户提交外部文章/教材/剧本 → 按内容路由轨道一/三/四
- 新模式 3+ 案例验证 → 升格为正式规则

---

## 参考文档

- `knowledge/craft/shanyin-screenwriting-methodology.md` — 横截面 / Ghost-Lie-Flaw / McKee
- `knowledge/market/douyin-formulas.md` — 爆款公式
- `foundation/theme-matrix.yaml` — 频道+四轴矩阵与参数合成 SSOT
- `knowledge/craft/theme-templates.md` — 规则模板量化参数
- `knowledge/quality/tier4-compliance.md` — 合规红线
- `knowledge/quality/originality-rules.md` — 改编模式原创性保护
- `foundation/constraints/script-format.yaml` — 字数与格式数值
- `knowledge/system/storyforge-runtime-methodology.md` — 生成过程控制（收敛停止/上下文加载）
