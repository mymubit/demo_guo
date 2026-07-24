# 项目向导工作台 W3 验收清单（2026-07-24）

> 设计：`docs/superpowers/specs/2026-07-24-project-workbench-wizard-design.md` §5 W3  
> 计划：`docs/superpowers/plans/2026-07-24-project-workbench-w3.md`

## 验收标准

| # | 标准 | 证据 | 结果 |
|---|------|------|------|
| 1 | 共用 `StageStatusPanel`（任务态/失败/生成成功/前置/下一步） | 六阶段页接入 | ☑ |
| 2 | 确认后显示下一阶段引导链接 | `resolveNextStageCta` + panel nextStep | ☑ |
| 3 | 页内冗余「项目设置」已去掉（Workbench 保留入口） | 六页无该 Link | ☑ |
| 4 | 确认 CTA 统一为「确认采用」（质检修订类除外） | Blueprint/Editor 文案 | ☑ |
| 5 | running 文案统一「进行中」 | 页测 | ☑ |

## 机跑

```text
npx vitest run src/pages/TopicPage.test.tsx \
  src/pages/BlueprintPage.test.tsx \
  src/pages/EpisodesPage.test.tsx \
  src/pages/ScriptEditorPage.test.tsx \
  src/pages/QualityPage.test.tsx \
  src/pages/DeliveryPage.test.tsx \
  src/components/workflow/StageStatusPanel.test.tsx \
  src/pages/projectLabels.test.ts
# 49 passed
```

## 手检

1. 确认选题后出现「去故事蓝图」引导条  
2. 阶段页顶栏不再有第三个「项目设置」  
3. 生成中状态显示「最近任务：进行中」  

## 向导三波次总结

| 波次 | 状态 |
|------|------|
| W1 工作台壳 | ✅ |
| W2 产物预览 | ✅ |
| W3 操作流 | ✅ |
