# 项目向导工作台 W2 — ArtifactPreview Implementation Plan

> **For agentic workers:** 按任务执行；未要求不 commit。

**Goal:** 共用 `ArtifactPreview`：默认可读结构，可切原始 JSON；替换阶段页裸 `<pre>`。

**Spec:** `docs/superpowers/specs/2026-07-24-project-workbench-wizard-design.md` §4 / §5 W2

## File map

| 文件 | 职责 |
|------|------|
| `utils/artifactDisplay.ts` | `flattenArtifactEntries` + 常用中文标签 |
| `components/ArtifactPreview.tsx` | 可读 / 原始 JSON 切换 |
| Topic/Blueprint/Episodes/Delivery | 接入 |
| 对应 tests | 切换与标签 |

### Task 1: flatten + labels
### Task 2: ArtifactPreview 组件 + test
### Task 3: 四页接入
### Task 4: 基线
