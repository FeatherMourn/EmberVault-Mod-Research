# CODE-0012 preview runbook

This is a future manual runbook; the current CODE-0012 delivery is a staging
plan and does not enable a game runtime experiment.

## Phase 1 — preview only

1. Keep the current `Architect_Mod/Current` designation unchanged.
2. Do not copy over the deployed native DLL. The staged module is
   `runtime/staging/ArchitectProductPathPreview.lua`; the authoritative data is
   `bridge/blueprint_ghost_identity_perturbation_manifest.json`.
3. The module defaults to `enabled=false` and is not loaded by `src/mod.lua`.
   A future authorized package may place this Lua/resource adapter in a separate
   staging mod directory (for example `Architect_Mod/Staging-Code0013`), enable
   the canary flag there, and leave `Architect_Mod/Current` untouched. It uses
   only source-anchored clone/append operations and fails closed on missing
   templates, ID collisions, unsafe payload sizes, or a missing RenderModel
   companion.
4. Launch normally and select each private canary through the vanilla
   Construction Hammer. Record whether the ghost matches its manifest pattern:
   CONTROL=A/A and GHOST_VARIANT=A/B are sufficient to discriminate preview
   identity without placing anything.

To restore, disable the staging directory and relaunch. Delete only the
staging package directory if desired; do not remove caches or alter vanilla
resources. No current file needs to be enabled or copied for this delivery.

## Phase 2 — optional disposable-world placement

Use a disposable test world only if preview-only results cannot distinguish the
remaining relationship. Place the minimum canaries needed: CONTROL plus
FINAL_VARIANT distinguishes final payload authority; GHOST_VARIANT distinguishes
ghost identity. Record expected versus observed final occupancy and collect the
manifest/bridge output. Never run this test in a valued world.

The expected result is evidence only. It must not be promoted to
`PRODUCT_PATH_PREVIEW_CONFIRMED` or `PRODUCT_PATH_PLACEMENT_CONFIRMED` until
the user supplies the corresponding live observations.
