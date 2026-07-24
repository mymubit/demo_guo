# P3-W1 Task 4 Report

## 完成项
- 新增 `utils/parseEpisodeHint.ts`：`parseEpisodeNumber` 支持 `episode_number` / `episode` 字段与「第 N 集」文案。
- `QualityPage` 每条 issue 增加「定位到正文」按钮，经 `useNavigate` 跳转 `/projects/:id/editor?finding=&episode=`。
- `IssueRow` 保留 `raw` 原始项；集号优先解析 raw，回退 title+detail。
- 扩展 `QualityPage.test.tsx`：mock `useNavigate`，覆盖带/不带 episode 的跳转。

## 验证
- `npm test -- --run src/pages/QualityPage.test.tsx` → 10 passed

## 未做
- 未 git commit（按 brief 跳过）
