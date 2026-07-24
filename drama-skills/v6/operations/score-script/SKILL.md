---
name: score-script
description: Score a specified version and episode range of a short-drama screenplay against the V6 quality dimensions with evidence and veto checks. Use for diagnostic scoring and revision triage; do not use to modify scripts, approve compliance, or prepare delivery.
---

# Score Script

Execute only through `operation.yaml` and expose every transaction stage.

1. Bind the command to an exact script version and episode range.
2. Separate review requests from system rules and versioned artifact reads.
3. Present the plan and scoring execution pack before evaluation.
4. Produce only a candidate quality report with evidence per dimension.
5. Validate calculations, evidence coverage, veto rules, scope, and version.
6. Commit only the report after confirmation; never modify the screenplay.

Never call V5, another operation, or a role. Invoke only the listed stateless capabilities.
