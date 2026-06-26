---
name: drama-master
version: "4.0.0"
description: "AI短剧创作总入口 v4.0。6个生产角色·2个独立裁判·1个可选交付工具。路由至 orchestration/fast-track 或 expert-track。Invoke for full drama workflow or stage routing."
tags: ["总入口", "创作", "路由", "全流程", "标准主链"]
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

# Drama Master — 创作总入口 v4.0

> **6 生产角色 · 2 独立裁判 · 1 可选交付工具 · Git SSOT**
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
   → topic-director 输出故事定调 + 市场判断 + 爆款策略
② 集数规模：10-20 / 30-50 / 50+
③ 目标平台：抖音 / 快手 / 小程序 / 通用
④ 当前进度：从零 / 有创意 / 有大纲 / 已有剧本
⑤ 模式：标准创作通道（6+2） / 专家通道（追加宣发交付工具）
```

---

## 创作模式

### 标准创作通道（6 生产 + 2 裁判）

见 `orchestration/fast-track.yaml`。顺序：

选题定调官 → 人物关系官 → 全剧架构官 → 分集设计官 → 剧本正文官（分批）→ 剧本修订官 → 剧本评分官 → 合规审查官

### 专家通道（标准主链 + 宣发交付）

见 `orchestration/expert-track.yaml`。在标准主链后追加：

- 宣发交付工具（定稿后）

---

## 阶段路由

| 阶段 | 角色 | 输出 |
|------|------|------|
| 选题定调 | topic-director | project_brief |
| 人物关系 | character-relations | character_bible |
| 全剧架构 | series-architect | series_outline |
| 分集设计 | episode-designer | narrative_plan |
| 正文创作 | script-writer（episode_range 分批） | episode_scripts |
| 返修精修 | revision-master | polished_script |
| 独立评分 | script-scorer | quality_report |
| 合规审查 | compliance-guard | compliance_report |
| 宣发交付 | delivery-tool（可选） | production_package |

---

## 直接调用

```
@drama-topic-director       @drama-character-relations
@drama-series-architect     @drama-episode-designer
@drama-script-writer        @drama-revision-master
@drama-script-scorer        @drama-compliance-guard
@drama-delivery-tool
```

---

## 长剧策略

1. series-architect 一次出全剧架构
2. episode-designer 分批输出分集设计
3. script-writer 每批 ≤5 集（`episode_range=1-5`）  
4. 每批：script-scorer 十维评分；低于 B 级由 revision-master 返修后再续写

---

## 参考文档

- `knowledge/shanyin-screenwriting-methodology.md` — 横截面 / Ghost-Lie-Flaw / McKee
- `knowledge/douyin-formulas.md` — 爆款公式
- `foundation/theme-matrix.yaml` — 四轴矩阵与规则模板映射
- `knowledge/theme-templates.md` — 规则模板量化参数
- `knowledge/tier4-compliance.md` — 合规红线
- `foundation/constraints/script-format.yaml` — 字数与格式数值
