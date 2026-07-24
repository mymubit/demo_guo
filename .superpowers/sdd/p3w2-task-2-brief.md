### Task 2: Export API

**Files:** `delivery_views.py`、`urls.py`、OpenAPI；Test API

- `POST .../delivery/export/docx/` IsAuthenticated owner
- 跑 delivery_gate；失败 400
- 成功 FileResponse attachment `*.docx`

