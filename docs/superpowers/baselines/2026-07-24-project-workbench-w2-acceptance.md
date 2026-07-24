# 项目向导工作台 W2 验收清单（2026-07-24）

> 设计：`docs/superpowers/specs/2026-07-24-project-workbench-wizard-design.md` §4  
> 计划：`docs/superpowers/plans/2026-07-24-project-workbench-w2.md`

## 验收标准

| # | 标准 | 证据 | 结果 |
|---|------|------|------|
| 1 | `ArtifactPreview` 默认可读预览，可切原始 JSON | `ArtifactPreview.test.tsx` | ☑ |
| 2 | 字段展平含中文标签 | `artifactDisplay.test` flatten | ☑ |
| 3 | Topic / Blueprint / Episodes / Delivery 接入 | 四页 + 回归测 | ☑ |
| 4 | 折叠未展开时不与摘要字段重复挂载 | 懒渲染 + 页测绿 | ☑ |

## 机跑

```text
npx vitest run src/components/ArtifactPreview.test.tsx \
  src/utils/artifactDisplay.test.ts \
  src/pages/TopicPage.test.tsx \
  src/pages/BlueprintPage.test.tsx \
  src/pages/EpisodesPage.test.tsx \
  src/pages/DeliveryPage.test.tsx
# 31 passed
```

## 手检

1. 选题/蓝图等打开「详细内容」→ 默认可读字段  
2. 点「原始 JSON」→ 缩进格式化 JSON  
3. 交付包装有「交付包详细内容」预览  

## 未做（W3）

- 阶段页生成/确认/下一步门禁文案统一打磨  
