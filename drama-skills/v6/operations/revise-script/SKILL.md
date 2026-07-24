---
name: revise-script
description: Revise a bounded episode range of an existing short-drama screenplay from explicitly accepted quality or compliance findings while preserving locked content and approved planning artifacts. Use for controlled screenplay repair; do not use for first drafts, global planning changes, or automatic acceptance of findings.
---

# Revise Script

Execute only through `operation.yaml` and expose every transaction stage.

1. Require explicit accepted findings, scope, base version, and preservation locks.
2. Load reports as read-only evidence and bounded adjacent context.
3. Present the revision plan and exact execution pack before writing.
4. Produce candidate changes only inside the requested episode range.
5. Validate locks, continuity, planning alignment, format, and base version.
6. Show all diffs and impacts; commit scripts and checkpoint atomically after confirmation.

Never call V5, another operation, or a role. Invoke only the listed stateless capabilities.
