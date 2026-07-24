# V3 P3-W3 产物版本回滚 Implementation Plan

> Continuous SDD; no human gate.

**Goal:** 列出 committed 版本并 rollback 复制为新 committed（R2 keys）。

**Rollback keys:** project_brief, story_bible, character_system, world_system, emotion_system, originality_report, episode_plan, episode_scripts

## Tasks

### Task 1: rollback service + API

**Files:** `orchestrator/artifact_rollback.py`; `api/v3/artifact_views.py`; urls; OpenAPI; `test_v3_artifact_rollback.py`

```python
def list_committed_versions(project, artifact_key) -> list[dict]: ...
def rollback_artifact(*, project, artifact_key: str, source_version: int, actor) -> V3ArtifactVersion:
    """Copy source committed payload to new version with status=COMMITTED; bump next_version."""
```

- GET `/api/v3/projects/{id}/artifacts/?artifact_key=`
- POST `/api/v3/projects/{id}/artifacts/rollback/` body `{artifact_key, source_version}`
- Validate key in ALLOWED set; source must be committed belonging to project

### Task 2: Frontend version UI

Minimal UI on ProjectOverviewPage or a section on Topic/Blueprint/Episodes/Editor:
- Prefer **ProjectOverviewPage**「版本回滚」面板：选 key → 列表 → 确认回滚
- services `artifacts.ts`; tests

### Task 3: 基线 → 立即 P3-W4

机跑 rollback tests + overview test；写基线；开 W4
