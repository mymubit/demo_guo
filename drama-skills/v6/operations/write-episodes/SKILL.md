---
name: write-episodes
description: Write a bounded range of short-drama screenplay episodes from approved versioned planning artifacts while maintaining continuity and emitting a memory checkpoint. Use for first-draft episode writing; do not use for plan generation, scoring, compliance-only review, or localized revision.
---

# Write Episodes

Execute only through `operation.yaml` and expose every transaction stage.

1. Record the requested range and user locks separately from system inputs.
2. Load exact artifact versions plus bounded adjacent context.
3. Present the plan and compiled execution pack before writing.
4. Produce candidate scripts and checkpoint without changing active artifacts.
5. Validate format, scope, continuity, planning alignment, locks, and version.
6. Show changes and downstream impacts; commit atomically only after confirmation.

Never call V5, another operation, or a role. Invoke only the listed stateless capabilities.
