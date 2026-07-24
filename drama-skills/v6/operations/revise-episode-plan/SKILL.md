---
name: revise-episode-plan
description: Revise a bounded range of existing short-drama episode plans while preserving explicit user locks and global story-bible invariants. Use when the user asks to change, tighten, reorder, or repair specific episode cards; do not use for first-time plan generation, screenplay dialogue edits, or global story-structure changes.
---

# Revise Episode Plan

Execute only through the V6 transaction defined in `operation.yaml`.

1. Parse the request into scoped changes, preservation locks, preferences, and unresolved questions.
2. Build and present a plan before model execution.
3. Load the approved story bible, current episode plan, adjacent episode context, and resolved settings.
4. Compile only the capabilities, atomic rules, knowledge fragments, and schema required for this call.
5. Produce a candidate for the requested episode range without writing the active artifact.
6. Validate schema, scope, preservation locks, field permissions, narrative invariants, adjacency, and base version.
7. Generate a field diff, semantic diff, change set, and downstream impact plan.
8. Commit atomically only after validation and confirmation.

Never import or call the V5 runtime. Never modify episodes outside the declared scope. Never change global story-bible structures from this operation.
