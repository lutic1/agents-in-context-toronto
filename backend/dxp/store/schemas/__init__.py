"""The `$jsonSchema` validators (A03, Story 9.2). Stub from A01.

A03 fills `VALIDATORS` with one `$jsonSchema` document per collection: grants,
policies, policy_sets, runs, admissions, decisions, actions, research_scopes, reports
(relationships embedded as related[]), memories, tasks, media and source_versions (V40).
`store.ensure_indexes()` applies each with validationLevel strict and validationAction error.
"""

VALIDATORS: dict[str, dict] = {}
