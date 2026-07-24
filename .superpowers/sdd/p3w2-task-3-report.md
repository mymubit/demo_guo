# P3-W2 Task 3 Report — DeliveryPage Word 下载 UI

**Status:** DONE  
**Date:** 2026-07-23

## Deliverables
| File | Action |
|------|--------|
| `services/http.ts` | + `responseType`；blob 错误体 JSON 解析 |
| `services/v3/delivery.ts` | + `exportDeliveryDocx`（POST blob） |
| `services/v3/delivery.test.ts` | + export 路径/options 断言 |
| `pages/DeliveryPage.tsx` | 「下载 Word」按钮 + PDF 脚注 + `downloadBlob` |
| `pages/DeliveryPage.test.tsx` | 门禁 disabled / 成功 blob 下载 |

## Verify
`npm test -- --run src/pages/DeliveryPage.test.tsx` → **6 passed**  
`npm run typecheck` → **0 errors**

## 未做
未 git commit（按要求跳过）。
