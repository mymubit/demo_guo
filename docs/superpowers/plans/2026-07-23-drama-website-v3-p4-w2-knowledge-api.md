# P4-W2 Knowledge API Implementation Plan

> Continuous SDD; no human gate.

**Goal:** Read-only knowledge from `drama-skills/knowledge/**` — list, get by path, search q.

## Deliver

1. `orchestrator/knowledge_catalog.py`:
   - `list_docs(q=None, section=None) -> list[{path, title, section, excerpt}]`
   - `read_doc(path) -> {path, title, content}` 
   - Path must resolve under knowledge root; reject `..` and absolute escapes
2. API GET `/api/v3/knowledge/` and GET `/api/v3/knowledge/doc/?path=`
3. OpenAPI + `test_v3_knowledge_api.py`
4. Baseline + roadmap P4-W2 ✅ → auto W3
