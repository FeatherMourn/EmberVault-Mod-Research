# Recipe schema discovery — 2026-09-28

The current build's reflected `keen::RecipeInfo` schema uses:

- `input` — an array of `RecipeInputResource` records; item quantities are under `input[*].itemStack.count`.
- `output` — an array of `RecipeItemStackResource` records; quantities are under `output[*].count`.
- `craftingDuration` — the duration field; the schema does not use the authoring alias `craftTime`.
- `workshopId` and `workshopGuid` — workstation identity fields.
- `requiredProps` — required property references.

The first runtime customization probe verified independent output-count editing. The bounded userdata-aware clone then verified independent edits to `input[*].itemStack.count`, `output[*].count`, and `craftingDuration` without a loader panic. Workstation, knowledge-requirement, actual in-game crafting completion, and save persistence remain unverified.

Evidence sources include the current build's generated Lua type registry and the isolated recipe customization sessions under `research/probe_sessions/`.
