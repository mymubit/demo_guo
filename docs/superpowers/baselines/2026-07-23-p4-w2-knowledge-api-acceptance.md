# P4-W2 Knowledge API 验收清单（2026-07-23）

> 计划：`docs/superpowers/plans/2026-07-23-drama-website-v3-p4-w2-knowledge-api.md`  
> 设计：`docs/superpowers/specs/2026-07-23-drama-website-v3-templates-knowledge-design.md`  
> 验收日：2026-07-23

## 验收标准

| # | 标准 | 证据 | 结果 |
|---|------|------|------|
| 1 | 只读扫 `DRAMA_SKILLS_ROOT/knowledge/**/*.md`；`section`=首路径段；根文件 section 为空 | `orchestrator/knowledge_catalog.py`；`test_list_includes_root_and_sectioned_docs` | ☑ |
| 2 | GET `/api/v3/knowledge/?q=&section=` → `{items:[path,title,section,excerpt]}` | `test_filter_by_section`；`test_search_q_matches_path_title_or_excerpt` | ☑ |
| 3 | GET `/api/v3/knowledge/doc/?path=` 返回 markdown；`..`/绝对路径 400；缺失 404 | `test_get_doc_by_path`；`test_reject_path_traversal`；`test_missing_doc_404` | ☑ |
| 4 | 需登录；禁止写盘 | `test_unauthenticated_401`；无 POST/PUT/DELETE | ☑ |
| 5 | OpenAPI 含 `/knowledge/**` | `docs/contracts/v3/openapi.yaml` | ☑ |

## API 路径

前缀：`/api/v3/`

| Method | Path | 权限 |
|--------|------|------|
| GET | `/knowledge/?q=&section=` | IsAuthenticated |
| GET | `/knowledge/doc/?path=` | IsAuthenticated |

## 机跑

```text
py -3 manage.py test apps.drama.tests.test_v3_knowledge_api --settings=config.settings.sqlite_test
```

预期：全部 OK。
