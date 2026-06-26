---
name: drama-master
version: "3.1.0"
description: "AI短剧创作总入口 v3.1。12角色·双轨编排·四轴题材·山音方法论。路由至 orchestration/fast-track 或 expert-track。Invoke for full drama workflow or stage routing."
tags: ["总入口", "创作", "路由", "全流程", "双轨"]
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

# Drama Master — 创作总入口 v3.1

> **12 角色 · 双轨编排 · 四轴题材 · Git SSOT**
>
> 流程 SSOT：`orchestration/fast-track.yaml` / `expert-track.yaml`  
> 角色 SSOT：`registry.yaml` + `roles/*/role.yaml`

---

## 启动方式

```
@drama-master 我要创作一部30集复仇短剧
@drama-master 从四轴矩阵推荐一个有爆款潜力的题材
@drama-master --stage=writing 从第6集开始继续写剧本
@drama-master [help] 查看角色列表和使用说明
```

---

## 启动问卷

```
① 题材：四轴矩阵（见 `foundation/theme-matrix.yaml`）或一句话创意
   → topic-planner 输出 genre_matrix + theme_code
② 集数规模：10-20 / 30-50 / 50+
③ 目标平台：抖音 / 快手 / 小程序 / 通用
④ 当前进度：从零 / 有创意 / 有大纲 / 已有剧本
⑤ 模式：快速通道（8） / 专家通道（12）
```

---

## 双轨模式

### 快速通道（8 核心角色）

见 `orchestration/fast-track.yaml`。顺序：

选题策划官 → 世界架构师 → 人设设计师 → 情节架构师 → 剧本执笔师（分批）→ 审稿官 → 质量报告官 → 合规守卫

### 专家通道（12 角色）

见 `orchestration/expert-track.yaml`。在快速通道基础上按需增加：

- 市场分析师（立项前）
- 叙事工程师（大纲后）
- 精修大师（剧本后）
- 制作发行师（定稿后）

---

## 阶段路由

| 阶段 | 角色 | 输出 |
|------|------|------|
| 战略选题 | market-analyst（可选）→ topic-planner | market_report + project_brief |
| 世界构建 | world-architect → character-designer | world_setting + character_bible |
| 剧情设计 | plot-architect → narrative-engineer（可选） | series_outline + narrative_plan |
| 剧本创作 | script-writer（episode_range 分批） | episode_scripts |
| 质量审查 | script-reviewer → quality-reporter → compliance-guard | review + quality + compliance |
| 精修 | polish-master（可选） | polished_script |
| 发行 | production-pack（可选） | production_package |

---

## 直接调用

```
@drama-topic-planner       @drama-world-architect      @drama-character-designer
@drama-plot-architect      @drama-script-writer        @drama-script-reviewer
@drama-quality-reporter    @drama-compliance-guard
@drama-market-analyst      @drama-narrative-engineer   @drama-polish-master
@drama-production-pack
```

---

## 长剧策略

1. plot-architect 一次出全剧大纲  
2. narrative-engineer 可选强化  
3. script-writer 每批 ≤5 集（`episode_range=1-5`）  
4. 每批：reviewer → quality-reporter；低于 B 级重写后再续写  

---

## 参考文档

- `knowledge/shanyin-screenwriting-methodology.md` — 横截面 / Ghost-Lie-Flaw / McKee
- `knowledge/douyin-formulas.md` — 爆款公式
- `foundation/theme-matrix.yaml` — 四轴矩阵与规则模板映射
- `knowledge/theme-templates.md` — 规则模板量化参数
- `knowledge/tier4-compliance.md` — 合规红线
- `foundation/constraints/script-format.yaml` — 字数与格式数值
