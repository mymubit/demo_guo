# 项目向导工作台 W3 Implementation Plan

> **Goal:** 统一阶段状态区与确认后「下一步」引导；去掉页内冗余「项目设置」。

**Spec:** `docs/superpowers/specs/2026-07-24-project-workbench-wizard-design.md` §5 W3

## 交付

1. `StageStatusPanel`：任务状态 / 失败 / 生成成功提示 / 前置阻断 / 确认后下一阶段链接
2. `resolveNextStageCta`：当前阶段 → 下一阶段 CTA
3. 六页接入；移除 PageShell「项目设置」；确认 CTA 尽量统一为「确认采用」
4. vitest + 基线
