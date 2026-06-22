---
name: drama-forge-evolution
version: 1.0.0
description: drama-forge 技能体系的自我进化协议。收集审稿评分数据，分析共性缺陷，生成技能文件更新提案，通过 git PR 实现技能进化。适用于用户提出技能优化、复盘分析、质量改进、或主动触发进化时使用。
platforms: [cursor, codex, trae]
---

# Drama Forge Evolution — 技能自我进化协议

> **这是元技能**：本技能不创作剧本，而是负责让其他 drama-forge 技能变得更好。

---

## 核心理念

`drama-forge-evolution` 实现了**基于证据的技能持续改进**机制：

```
创作输出 → quality-reviewer 评分 → evolution-analyst 分析
    → 缺陷模式识别 → 技能文件更新提案
    → git PR 审查 → 合并 → 技能进化 → 下一代创作更好
```

这是一个 **git 原生（Git-Native）** 的进化系统——技能文件存在 git 仓库中，进化历史即 git 提交历史，回滚即 `git revert`。

---

## 适用场景

- 完成3+个完整创作项目后，主动做复盘优化
- quality-reviewer 连续输出低分（<70）
- 某个创作维度反复出现同类问题
- 用户希望技能体系"越用越好"
- 定期（如每月）做技能健康检查

---

## 工作流程

### Phase 1：证据收集

```
1. 收集 quality-reviewer 的 JSON 审稿报告
2. 提取所有缺陷记录（defects 数组）
3. 统计高频缺陷（出现≥2次的 dimension+description 组合）
4. 计算各维度平均分变化趋势
```

**证据收集命令**（Cursor/Codex）：
```
读取 `审稿报告*.json` 文件，
提取 defects 数组，
按 dimension 分组统计 count 和 avg_score。
```

### Phase 2：根因分析

```
1. 将高频缺陷映射到负责角色
2. 阅读对应角色的技能文件（roles/*.md）
3. 识别：规范中缺失/模糊/误导的条目
4. 评估：变更影响范围（只影响一个角色 vs 跨角色）
```

**维度 → 角色映射**：

| 审稿维度 | 负责角色文件 |
|---------|-------------|
| format | scene-director.md + dialogue-writer.md |
| structure | plot-architect.md |
| character | character-designer.md |
| emotion | emotion-engineer.md |
| commercial | drama-director.md |

### Phase 3：生成进化提案

生成 `EVOLUTION_PROPOSAL_GEN{N}.md` 文件：
- 清晰标注修改哪个文件、哪一行
- 原内容 vs 新内容（diff 风格）
- 修改理由与预期效果

### Phase 4：执行进化（需确认）

```bash
# 1. 创建进化分支
git checkout -b drama-forge/evolution-gen-{N}

# 2. 修改对应技能文件
# 按 EVOLUTION_PROPOSAL_GEN{N}.md 执行变更

# 3. 更新版本信息
# 在所有修改的文件头部：evolution_generation +1
# 更新 last_evolved 日期

# 4. 记录进化历史
# 追加 CHANGELOG.md

# 5. 提交推送
git add .cursor/skills/drama-forge/
git commit -m "feat(drama-forge): evolution gen-{N} - {核心变更摘要}"
git push -u origin drama-forge/evolution-gen-{N}

# 6. 创建 PR（等待人工审批）
# PR 标题：[Drama Forge Evolution] Gen {N}: {变更摘要}
# PR 描述：引用 EVOLUTION_PROPOSAL_GEN{N}.md 内容
```

---

## 工作原则

1. **最小变更**：每次进化只修改1-3个条目，禁止大规模重写
2. **证据驱动**：每个变更必须有具体的质量数据支撑（几个项目、什么分数）
3. **人工审批**：变更通过 PR 等待审批，不直接 force push
4. **跨平台同步**：更新 `.cursor/skills/` 后检查 `.codex/` 和 `.trae/rules/` 是否需要同步
5. **可测试**：进化后用1-2个创作项目验证效果，记录到 CHANGELOG

---

## 进化成熟度评估

技能体系进化成熟度分级：

| 代数 | 成熟度 | 特征 |
|------|--------|------|
| Gen 0 | 初始版本 | 基于知识资产设计，未经实战验证 |
| Gen 1-3 | 早期进化 | 修复明显的格式和结构规范缺失 |
| Gen 4-7 | 中期进化 | 优化人物和情绪设计细粒度规范 |
| Gen 8+ | 成熟进化 | 专项平台/题材/风格的精细化规范 |

---

## 分析前置步骤

1. 读取 `quality-reviewer` 输出的 JSON 报告
2. 读取当前各角色技能文件（roles/*.md）
3. 读取 `CHANGELOG.md`（如已存在）了解历史进化记录
4. 读取 `backend/apps/skill/evolution/services.py` 了解后端进化机制（可复用逻辑）

---

## 详细参考

- 进化分析师角色规范：`../drama-forge/roles/evolution-analyst.md`
- 进化提案模板：`REFERENCE.md`
- 后端进化机制（Django）：`backend/apps/skill/evolution/`
