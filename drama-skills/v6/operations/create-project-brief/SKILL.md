---
name: create-project-brief
description: Create or replace a versioned short-drama project brief from a creative request, audience, platform, format, and explicit constraints. Use for project initiation or approved brief regeneration; do not use to write a story bible, episode plan, or screenplay.
---

# Create Project Brief

Execute only through `operation.yaml` and expose every transaction stage.

1. Record user inputs separately from system inputs and versioned reads.
2. Present the plan and compiled execution pack before generation.
3. Produce a candidate project brief without mutating the active version.
4. Validate constraints, originality boundary, schema, scope, and base version.
5. Show the change set and downstream impact plan.
6. Commit atomically only after successful validation and confirmation.

Never call V5, another operation, or a role. Invoke only the listed stateless capabilities.
