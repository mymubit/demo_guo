# V3 P3-W2 后端 Word 导出 Implementation Plan

> Continuous SDD; no human gate. REQUIRED: subagent-driven-development.

**Goal:** `POST /api/v3/projects/{id}/delivery/export/docx/` 经 delivery 门禁后返回 `.docx`；Delivery UI 下载按钮 + PDF 打印说明。

**Tech:** `python-docx==1.1.2`（钉版本）。

**Spec:** phase-3 design 导出轨 E3 / 方案 2

## Global Constraints

- 无支付；无 PDF 服务端
- 门禁与 prepare_delivery 一致
- Commit 跳过；`DRAMA_SKILLS_ROOT` → drama-skills
- `py -3 manage.py test … --settings=config.settings.sqlite_test`

## Tasks

### Task 1: 加依赖 + docx 生成服务

**Files:** `backend/requirements*.txt` or pyproject；Create `orchestrator/docx_export.py`；Test `test_v3_docx_export.py`

```python
def build_episode_scripts_docx(*, project_title: str, scripts_payload: dict) -> bytes:
    """返回 docx 文件字节；含标题与各集正文。"""
```

- [ ] TDD：bytes 以 PK\\x03\\x04 开头或 Document 可读段落含标题
- [ ] pip/requirements 加 python-docx==1.1.2
- [ ] Implement

### Task 2: Export API

**Files:** `delivery_views.py`、`urls.py`、OpenAPI；Test API

- `POST .../delivery/export/docx/` IsAuthenticated owner
- 跑 delivery_gate；失败 400
- 成功 FileResponse attachment `*.docx`

### Task 3: DeliveryPage UI

**Files:** `DeliveryPage.tsx` + test；`services/v3/delivery.ts`

- 按钮「下载 Word」调用导出 API（blob download）
- 脚注：「PDF 请使用浏览器打印为 PDF」
- 门禁未通过时 disabled

### Task 4: 基线

机跑 backend export tests + DeliveryPage test + typecheck  
基线 `docs/superpowers/baselines/2026-07-23-p3-w2-docx-export-acceptance.md`  
更新 roadmap → **立即开 P3-W3**
