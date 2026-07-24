# W6 Task 3 报告：`/api/v2` 不可达

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W6 — `/api/v2` 统一 410 Gone  
**Commits:** none（用户明确跳过）  
**Brief:** `.superpowers/sdd/w6-task-3-brief.md`  
**Plan:** `docs/superpowers/plans/2026-07-23-drama-website-v3-w6-billing-legacy-cut.md` Task 3

---

## What I Implemented

### 1. `apps/drama/api/v2_gone.py`（新建）

- `V2GoneView`：`get/post/put/patch/delete` → HTTP 410
- 信封：`{code: 410, message: "旧接口已下线，请使用 /api/v3/", data: null}`
- `AllowAny` + 空 `authentication_classes`，未登录亦 410（非 401）

### 2. `config/urls.py`

- 移除 `include("apps.drama.v2_urls")`
- 挂载 `api/v2/` 与 `api/v2/<path:rest>` → `V2GoneView`
- 注释改为产品 API `/api/v3/`，旧 v2 统一 410（去掉「V6 Studio 是唯一业务入口」）

### 3. 测试 `test_v2_gone.py`

- `/api/v2/studio/bootstrap/` → 410，message 含 `/api/v3`
- `/api/v2/` GET → 410
- `/api/v2/studio/anything/` POST → 410

未删除 `v2_*` 模块（留给 Task 5）；未 git commit。

---

## TDD / Verification

```bash
cd backend
py -3 manage.py test apps.drama.tests.test_v2_gone --settings=config.settings.sqlite_test -v 2
```

**结果：** 3 passed；exit 0

---

## Files Changed

| 路径 | 操作 |
|------|------|
| `backend/apps/drama/api/v2_gone.py` | 新建 |
| `backend/config/urls.py` | 修改（去 v2 include，挂 410） |
| `backend/apps/drama/tests/test_v2_gone.py` | 新建 |
| `.superpowers/sdd/w6-task-3-report.md` | 本报告 |

---

## Concerns

1. `v2_*` 与旧测试仍在仓库，仅路由不可达；Task 5 删文件前勿再 include。
2. 仍引用 `/api/v2` 的前端/集成客户端会立刻收到 410，需靠 W6 后续删 studio 与清依赖对齐。
3. `code=410` 与 HTTP status 对齐；若全局客户端只认 `code===0` 业务成功则行为正确。

---

## Reviewer Verdict

**Spec:** ✅  
**Quality:** Approved

- `config/urls.py` 已移除 `include("apps.drama.v2_urls")`，改挂 `V2GoneView`（`api/v2/` + catch-all）。
- `/api/v2/studio/**` 实测 410，信封 `code=410`，message 含 `/api/v3/`；未登录亦 410（AllowAny + 空 auth）。
- `v2_urls.py` / `v2_views.py` / `v2_service.py` / `v2_serializers.py` 均仍在。
- `test_v2_gone` 3/3 通过（sqlite_test，exit 0）。
- urls 注释已去「V6 Studio 唯一入口」表述。

无阻塞项。`backend/README.md` 仍写 `/api/v2/studio/`，属文档滞后，非本 Task 范围。
