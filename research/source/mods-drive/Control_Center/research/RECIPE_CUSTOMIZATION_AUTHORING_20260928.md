# Recipe customization authoring guide — 2026-09-28

Recipe customization is currently `research-only` for the target build. The
compiler validates plans before packaging, and the runtime helper edits a
bounded clone rather than the donor recipe.

## Supported authoring fields

The current `RecipeInfo` field names are:

- `input[*].itemStack.count` for ingredient quantities.
- `output[*].count` for output quantities.
- `craftingDuration` for craft time.
- `workshopId` and `workshopGuid` for workstation identity.
- `requiredProps` for required property references.
- `knowledgeRequirement` for the unlock query.
- `debugName` and `showIsImportantLabel` for metadata.

The offline compiler rejects non-object recipe plans, malformed input/output
arrays, non-positive item IDs or counts, negative durations, invalid workstation
IDs, and invalid requirement structures before a loader probe is produced.

## Runtime safety rules

Use `clone_recipe_for_edit` or `edit_recipe` on a donor recipe, assign a new
recipe ID, and register the clone. Never edit the donor object in place. To
transfer an unlock query, use `replace_knowledge_requirement(clone,
requirement_donor)`; the donor must expose a populated `knowledgeRequirement`.

Every generated probe must remain isolated and marked `research-only`. Remove
the probe and restore the stable profile after each run.

## Evidence status

Runtime evidence currently verifies independent editing of duration, ingredient
quantity, output quantity, workstation ID, required properties, and clearing a
knowledge requirement. Replacement with a different populated query, actual
craft completion, catalog unlock behavior, and save persistence remain
unverified. These capabilities must not be promoted to stable until fresh
same-build in-game evidence exists.
