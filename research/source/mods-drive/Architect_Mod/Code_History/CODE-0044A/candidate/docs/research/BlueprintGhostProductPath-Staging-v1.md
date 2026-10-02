# CODE-0012 — Vanilla blueprint/ghost product path staging

Status: `PRODUCT_PATH_STAGING_READY` / `OFFLINE_STAGING_ONLY`.
No EML call, process access, native hook, injection, deployment, resource write,
or world mutation is performed by this milestone.

## Evidence recovered in the working tree

The Architect-owned `src/mod.lua` contains the historical path used by the
proven standalone custom blueprint:

1. Clone an existing `keen::ItemInfo` with `game.assets.create_resource` and
   restore a private item identity.
2. Append a same-dimension `VoxelBlueprintItem` to the discovered blueprint
   registry, then replace only its bounded payload bytes in place.
3. Clone a same-dimension `keen::VoxelModelResource`, write preview values
   (`18` visible / `0` empty), and set `isTerrain=false`.
4. Clone the same-GUID `keen::RenderModel` companion for the private preview.
5. Link the validated ItemInfo into `ItemRegistryResource.itemRefs` only after
   collision, dimensions, preview, and payload checks pass.

The source also declares `MAX_SAFE_EML_PLACEMENT_BYTES = 8`; larger nested
Array<u8> payloads are intentionally rejected because historical allocator
failures are unresolved. The staging planner therefore uses only 4×4×4
compressed canaries (64 voxels, 8 bytes) and never resizes an array.

## What is implemented

`tools/ArchitectProductPath/product_path_staging.py` turns those exact source
anchors into a deterministic plan, manifest, and disabled-by-default Lua
package. It generates two private patterns (corner shell A and central block B),
four private canary variants, collision checks, payload/preview hashes, and
explicit source/evidence labels. The Lua package reuses the same source-backed
EML calls only when its explicit `activate()` entry point is enabled; the
planner itself never invokes EML. Symbolic UUIDs are diagnostics only and are
not passed to an asset API.

The generated package is not loaded by the current mod, and its activation is
off by default. It fails closed on missing templates, ID collisions, unsafe
payload sizes, or a missing RenderModel companion; it performs no placement
automation. Runtime GUID creation and registry publication occur only inside an
explicit future test session, not during this offline run. Missing source
anchors cause `BLOCKED_MISSING_PROVEN_SOURCE` rather than a fabricated
implementation.

The matrix is:

| Variant | Final | Ghost | Preview-only discrimination | Disposable placement |
|---|---|---|---:|---:|
| CONTROL | A | A | yes | no |
| GHOST_VARIANT | A | B | yes | no |
| FINAL_VARIANT | B | A | no | yes |
| CROSS_WIRED | A | B | no | yes |

All variants use private resource identities and leave vanilla resources
untouched. `CROSS_WIRED` is only represented as a private plan because the
proven path supports a private blueprint plus private VoxelModel/RenderModel
pair; it does not imply that any live cross-resource wiring has been tested.

Machine-readable output:
`bridge/blueprint_ghost_identity_perturbation_manifest.json`.
