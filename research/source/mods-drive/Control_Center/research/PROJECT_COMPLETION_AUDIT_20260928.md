# Project completion audit — 2026-09-28

This report is an evidence-based snapshot of the complete remaining-work plan.
It is not a 100% completion claim.

## Current verified foundation

- Stable Control Center release baseline: 1.0.2.
- Target game build: `1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z`.
- Full automated suite: 589 tests passing.
- Milestone verifier: all 49 gates passing.
- Stable live profile: ready, isolated, and free of research modules.
- Furniture cloning: verified for the proven donor matrix, including a distinct
  catalog slot and placed interaction behavior.
- Latest visual-substitution session: clone and UI registration succeeded
  without panic, and the replacement model assignment was accepted; human-
  visible placed-object appearance and fresh-launch persistence were not
  captured, so the visual route remains experimental/research-only.
- Offline builder workflow, recovery, quarantine, compatibility checks, tuning
  inventory, documentation, and authoring templates: implemented and gated.
- EML Lua API `1.2` is now reported and detected from fresh runtime logs;
  health reports and dashboard compatibility use the observed version. The
  API evidence is fresh-session/build-pinned and does not claim a cached mod
  body executed.
- The isolated quest prototype evidence chain is now fail-closed and milestone
  gated: standalone typed identity editing, donor-preserving typed-array
  insertion, temporary runtime attachment, and probe restoration are verified.
  Visible journal behavior, persistence, completion/rewards, and multiplayer
  authority remain explicitly unverified.
- The actor-sequence research chain is also fail-closed and milestone gated:
  a 41-event graph, donor-preserving unique clone, exact event/type parity,
  one isolated attack-reference reassignment, and cleanup are verified. No
  changed AI behavior, new enemy archetype, or spawn registration is claimed.
- EML API 1.2 adds bounded metadata enumeration and avoids whole-database
  preallocation for type-specific queries. A fresh isolated session safely
  identified animation-graph, actor-sequence, voxel-world, water-world, and
  world-material donors without decoding payloads; the profile was restored.
- A subsequent single-donor animation-graph session safely read the typed
  108-node payload, hierarchy, bone-slot mapping, input IDs, and root nodes.
  Its nodes and 32 dependency GUIDs are fully inventoried. EML API 1.3 resolves
  those GUIDs to 42 typed identities without decoding payloads. No attachment
  or mutation occurred; identity cloning remains open.

## Capability status

| Area | Status | Evidence required for promotion |
|---|---|---|
| Furniture clone/recipe/layout foundation | verified | Continue fresh-session regression and rollback checks. |
| Custom localization | experimental | Fresh-session visible label readback in catalog, item info, recipe, and placement UI. |
| Custom icons/materials/textures/colors | research-only | Same-build runtime rendering and recoverable failure evidence. |
| Clone-only model substitution | verified | Separate catalog slot, visible placed object, fresh-launch persistence, and rollback evidence are recorded. |
| Original mesh/asset import | research-only | Registration, dependency resolution, visible use, and rollback, or reproducible engine boundary. |
| Tuning settings | experimental | Additional family-by-family runtime verification with rollback. |
| Builder assistance | verified offline | Optional in-game placement authority study. |
| New resources and gameplay graphs | research-only | Donor schema inventory followed by isolated runtime prototypes. |
| Multiplayer authority | unsupported by verified route | Authoritative server/replication hook and peer-visible evidence. |
| Loader hardening and recovery | experimental | Repeated live launch/shutdown and current-source installer parity. |

## Release and packaging status

- Portable artifact and documentation bundle are hash-verified.
- Clean-install, upgrade-preservation, uninstall, and installer smoke evidence
  exists for the recorded installer artifact.
- Installer source includes the current safety and capability documents.
- The portable executable and installer were rebuilt from the current source.
  Inno Setup 6.7.3 was discovered in the user's local Programs directory after
  the release script was upgraded to search installed locations outside PATH.
- Isolated installation verified that the installer contains the exact
  portable executable hash, preserves a user profile during upgrade, and
  removes only owned files during uninstall.

## Remaining completion gates

1. Establish reliable fresh-session logging and repeat localization evidence.
2. Complete catalog-preview/icon research verdicts with matching screenshots,
   logs, cleanup, and stable-profile restoration.
3. Continue controlled visual graph tracing and either verify original asset
   use or document the exact engine boundary.
4. Runtime-verify additional tuning families and preserve rollback evidence.
5. Run the documented read-only research tracks for interactions, AI, quests,
   animation/world generation, and multiplayer authority; keep unsupported
   boundaries explicit.
6. Re-run the final requirement-by-requirement audit with current screenshots,
   logs, manifests, evidence, and release artifacts.
