# Catalog preview boundary — build 1076226

## Confirmed result

The `catalog_icon_fallback_probe_20260928` session registered a new furniture
item, cloned its recipe UI set, and assigned a known-good vanilla
`UiTextureResource` to `ItemInfo.iconImage`. The runtime log recorded the new
typed reference after assignment and the session completed without a panic.
The corresponding in-game screenshot still showed the additional Carpenter
slot as an empty tile.

Evidence: `research/probe_sessions/catalog_icon_fallback_20260928_r1.json` and
the log segment beginning at byte `107980` in the 2026-09-28 EML log.

## Interpretation

## Menu-entry schema clarification — 2026-09-29

The current build's reflected `FbUiBundle` crafting schema was traced through
the serialized bundle and type registry:

- `FbUiCraftingRecipeTree` contains `groups`.
- `FbUiCraftingRecipeGroup` contains `groupId`, `icon`, `label`, and `sets`.
- `FbUiCraftingRecipeSet` contains `label`, `recipeSetId`, and `entries`.
- `entries` is a typed `BlobArray<keen::RecipeId>`; there is no per-entry icon,
  model, preview, or thumbnail field.

This rules out adding a missing per-entry preview field as the direct fix for
the blank custom tile. The remaining catalog-preview boundary is the clone's
`ItemInfo.iconImage`/`iconModel`/`iconScene` resolution or native renderer
requirements, not the recipe-set entry schema.

This separates three states that must not be conflated:

1. `iconImage` reference assignment is accepted by the runtime.
2. The `FbUiBundle` recipe set and entry are registered.
3. The catalog renderer has enough preview metadata to draw a tile.

The first two are evidenced. The third is not. This is a UI presentation
boundary, not evidence that the item registration or recipe path failed.

## Next candidate matrix

The ItemInfo schema exposes `iconModel`, `iconScene`, `iconRenderOffset`,
`iconRenderCookingScale`, `iconRenderGlobalScale`, `overrideSceneExposure`, and
`fitToItemModelBoundingBox`, with the model/scene fields disabled when
`iconImage` is present. The next probe should compare one variable at a time:

- image-only with donor preview metadata;
- model/scene-only with all icon-image fields cleared;
- model/scene plus render scale/offset/exposure copied from a known furniture
  donor;
- cloned UI entry fields beyond the recipe link, especially any preview/icon
  reference fields exposed by the containing `FbUiBundle` schema.

Each candidate must use a new item/recipe identity, a fresh EML session on the
same build, and a screenshot-based render verdict. Runtime assignment alone
must remain `research-only`.

The corrected zero-GUID full workflow completed icon fallback assignment, clone
discovery, and recipe editing without a panic. Runtime assignment is now
verified, but catalog rendering and placement remain unverified because no
menu screenshot was captured in that session.

The probe generator now supports an explicit `--clear-icon-fallbacks` variant.
That candidate clears `iconModel` and `iconScene` before assigning `iconImage`,
allowing the next runtime run to distinguish mutually exclusive icon-mode
requirements from a renderer or resource-resolution failure. The original
donor-preserving candidate remains available for comparison.

The first live cleared-fallback run reached the cloned `ItemInfo` but emitted
no preview-assignment record after the fallback-clear operation. It was
cleaned up without a panic; the result is inconclusive and remains
research-only. A smaller bounded field-assignment probe was then run: the
all-zero GUID representation was accepted for both `iconModel` and
`iconScene`, while `nil` was not safely usable. A full catalog test using the
zero-GUID representation is still required.

## Safety rule

Do not enable this probe in the live stable profile. The verified profile is
restored after each research run, and the capability matrix remains
research-only until a catalog tile is visibly rendered and the placed object
is separately verified.

The next full menu attempt using the corrected zero-GUID variant reached the
game but produced the known EML `panic in a function that cannot unwind`
dialog before the catalog could be opened. The probe was removed and the run
is recorded as a crash verdict. The safe next step is to split the workflow
into registration-only and menu-only probes before another visual test.

## Registration-only split result — 2026-09-29

The split registration-only probe was corrected to insert the independent
`ItemInfo` clone into `ItemRegistryResource.itemRefs` and to append its debug
name to the parallel `dbgNames` array. A fresh log-only session then verified:

- item registry count increased from 3520 to 3521;
- the debug-name array remained aligned at 3521;
- zero-GUID `iconModel`, `iconScene`, and `iconImage` assignments were accepted;
- post-registration discovery found the new item;
- no recipe or UI mutation occurred;
- no panic dialog was observed;
- the research probe was removed afterward.

Evidence: `research/probe_sessions/catalog_preview_registration_only_20260929_r2_runtime_evidence.json`.

This removes item-registry insertion and post-registration discovery as the
current blocker. The remaining question is specifically native menu/catalog
membership and rendering. The next test should keep registration isolated,
then add only the smallest known recipe/UI link needed to open the menu and
capture a screenshot.
