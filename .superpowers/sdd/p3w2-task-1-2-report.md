# P3-W2 Task 1+2 Report — docx builder + export API

**Status:** DONE  
**Date:** 2026-07-23

## Deliverables
| File | Action |
|------|--------|
| `backend/requirements.txt` | + `python-docx==1.1.2` |
| `orchestrator/docx_export.py` | Created — `build_episode_scripts_docx`（script/scenes） |
| `api/v3/delivery_views.py` | + `V3DeliveryExportDocxView`（gate→400 / FileResponse） |
| `api/v3/urls.py` | + `delivery/export/docx/` |
| `docs/contracts/v3/openapi.yaml` | + export path |
| `tests/test_v3_docx_export.py` | 5 cases（unit + gate fail + success + 404） |

## Verify
`py -3 manage.py test apps.drama.tests.test_v3_docx_export --settings=config.settings.sqlite_test` → **5 passed**

## 未做
未 git commit（按要求跳过）；Task 3 UI / Task 4 基线未做。
