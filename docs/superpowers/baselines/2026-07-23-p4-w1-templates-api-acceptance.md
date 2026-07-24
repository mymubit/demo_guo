# P4-W1 Templates API 验收清单（2026-07-23）

> 计划：`docs/superpowers/plans/2026-07-23-drama-website-v3-p4-w1-templates-api.md`  
> 设计：`docs/superpowers/specs/2026-07-23-drama-website-v3-templates-knowledge-design.md`  
> 验收日：2026-07-23

## 验收标准

| # | 标准 | 证据 | 结果 |
|---|------|------|------|
| 1 | 模型 `V3ProjectTemplate` + `drama_v3_project_template`；`V3Project.settings` JSONField | migration `0023_v3_project_template_and_settings` | ☑ |
| 2 | GET `/api/v3/templates/` → `{builtin, custom}`；builtin 来自 `theme-matrix#preset_templates` | `test_v3_templates_api.test_list_builtin_and_custom` | ☑ |
| 3 | POST/PATCH/DELETE `/api/v3/templates/custom/` 仅 staff（`DramaConfigWritePermission`） | `test_staff_crud_custom_template`；`test_non_staff_write_forbidden` | ☑ |
| 4 | create_project 可选 `theme_code` / `template_id`，写入 `settings.template_seed` | `test_create_project_with_theme_code_seeds_settings` 等 | ☑ |
| 5 | OpenAPI 含 `/templates/**`；CreateProjectRequest 扩展字段 | `docs/contracts/v3/openapi.yaml` | ☑ |

## API 路径

前缀：`/api/v3/`

| Method | Path | 权限 |
|--------|------|------|
| GET | `/templates/` | IsAuthenticated |
| POST | `/templates/custom/` | staff |
| PATCH | `/templates/custom/{id}/` | staff |
| DELETE | `/templates/custom/{id}/` | staff |

建项：`POST /projects/` 可选 `template_id` 或 `theme_code`（互斥）。

## 机跑

```text
py -3 manage.py test apps.drama.tests.test_v3_templates_api --settings=config.settings.sqlite_test
```

预期：全部 OK。
