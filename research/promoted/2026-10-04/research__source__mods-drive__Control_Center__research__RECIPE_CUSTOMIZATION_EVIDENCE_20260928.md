# Recipe customization runtime evidence — 2026-09-28

An isolated probe cloned the bed donor and attempted three edits on the independent recipe.

- Output quantity: verified. The cloned output count changed to `2`.
- Craft time: rejected safely because the furniture recipe has no top-level `craftTime` field.
- Ingredients: rejected safely because the furniture recipe has no top-level `ingredients` field.
- Clone registration, registry growth, UI-set cloning, and one UI link all succeeded.
- No panic or loader error occurred.

This establishes partial runtime support rather than universal recipe customization. Ingredient and craft-time support require donor-specific schema discovery and must remain research-only until verified. Structured evidence is in `research/probe_sessions/recipe_customization_runtime_evidence_20260928.json`.
