# P4-W1 Templates API Implementation Plan

> Continuous SDD; no human gate.

**Goal:** builtin presets from theme-matrix + V3ProjectTemplate staff CRUD + create_project accepts template.

## Tasks

### Task 1: Model V3ProjectTemplate + migration

Fields: id UUID, name, theme_code, label_zh, dims JSON, description, created_by FK, created_at, updated_at. db_table drama_v3_project_template.

### Task 2: templates service + API

- `list_builtin_templates()` parse theme-matrix preset_templates via skills loader / yaml
- GET `/api/v3/templates/` auth → `{builtin, custom}`
- POST `/api/v3/templates/custom/` staff
- PATCH/DELETE `/api/v3/templates/custom/{id}/` staff
- OpenAPI + tests `test_v3_templates_api.py`

### Task 3: create_project 挂钩

- CreateProjectSerializer 可选 `template_id` (custom UUID) 或 `theme_code` (builtin)
- On create: store in project — prefer JSONField on V3Project if exists, else create initial topic draft / settings key `template_seed`
- Check V3Project model for settings field; minimal: put seed into result_payload and a `V3ArtifactVersion` candidate project_brief stub OR project field `meta` JSON

Inspect models and pick smallest hook: e.g. `V3Project` add `template_seed` JSONField nullable.

### Task 4: baseline W1 → auto W2

Tests green; write baseline stub; continue W2.
