# W2 Task 6 审查：前端 Topic 页

**Date:** 2026-07-23  
**Scope:** `TopicPage.tsx`、`services/v3/topic.ts`（只读审查）  
**Verdict — Spec:** ✅  
**Verdict — Quality:** Approved

---

## Spec 对照

| 要求 | 结果 |
|------|------|
| 中文 UI（生成简报/重新生成/确认采用/草稿/状态） | ✅ 全中文标签与提示 |
| `generate` → 轮询 `latest_run` 至终态 | ✅ `refetchInterval: 2000`（`queued\|running`） |
| 有 candidate 时「确认采用」 | ✅ `canConfirm` + `confirmTopicBrief` |
| 可选 textarea 编辑 draft + 保存 | ✅ JSON 编辑 + `saveTopicDraft` + `use_draft` 勾选 |
| 已确认/候选摘要（标题/卖点/受众，否则 JSON「详细内容」） | ✅ `BriefSummary` |
| 无 operation ID / 配方 ID | ✅ UI 与 service 均无 `operation.*`、`create-project-brief` 等 |
| service 四接口对齐 Task 5 API | ✅ GET/PUT draft/POST generate/POST confirm |
| 组件测 mock service + typecheck | ✅ 6 tests PASS；typecheck PASS |

---

## 实现要点

**`topic.ts`** — 薄封装，路径 `/api/v3/projects/{id}/topic/`，无业务泄漏。

**`TopicPage.tsx`** — React Query 拉状态；generate/confirm/draft 三 mutation；运行中禁用生成并显示「自动刷新中…」；不渲染 `command_type`、run UUID、artifact_key。

---

## 质量备注（非阻塞）

1. 测试未断言 `refetchInterval` 行为，也未覆盖「确认时使用草稿」路径。
2. 有摘要时仍展示「详细内容」折叠区——符合 spec，体验可接受。
3. 草稿为原始 JSON textarea，与 W2 最小实现一致。

---

## 验证

```text
npm test -- src/pages/TopicPage.test.tsx  → 6 passed
npm run typecheck                         → PASS
```
