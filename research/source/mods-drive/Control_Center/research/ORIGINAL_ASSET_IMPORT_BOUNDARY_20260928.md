# Original asset import boundary — 2026-09-28

## Current result

The platform can inspect, hash, package, and dependency-check PNG, glTF/GLB,
OBJ, audio, and related project files. These operations do not prove that the
Enshrouded client consumes a newly imported mesh or texture.

External evidence now exists from
[EnshroudedBlenderTools](https://github.com/Baik90/EnshroudedBlenderTools) for
KFC3 RenderModel import/export and EML mod-folder generation. This narrows the
research boundary substantially, but remains build-targeted external evidence
until Control Center records its own isolated runtime session.

## External handoff findings — 2026-09-29

The upstream project documentation now gives us a concrete handoff contract:

- It exports a new `RenderModel`, entity template, `ItemInfo`, and recipe by
  cloning an existing placeable base.
- It writes an EML mod folder containing `mod.json`, `validation.json`,
  `render_data.bin`, `src/mod.lua`, optional textures, and an optional icon.
- It supports topology-preserving replacements and full-topology replacements,
  with the latter limited to 65,535 generated vertices.
- It can export isolated material copies with custom textures when the target
  material already has the relevant slot, the original dimensions and format
  are retained, and `texconv.exe` is available.
- It can import and export the supported primitive collider shapes, but the
  collider count and shape set must remain unchanged.
- It explicitly reports that custom item icons are exported experimentally but
  remain blank in the game UI because the UI texture registration route is not
  solved.

This means the next Control Center integration should accept and validate the
generated mod-folder contract as a research-only import package. It must not
claim that the package is runtime-ready until our own target-build session
proves registration, placement, visual rendering, persistence, and rollback.
The upstream documentation is evidence of an export route, not evidence that
the current Control Center or current Enshrouded build consumes every output.

## Upstream README refresh — 2026-09-29

The current upstream README adds several constraints that should be preserved
by future authoring and validation work:

- The exporter can import one or all available LODs, but currently uses the
  same generated replacement mesh for every target LOD.
- Full-topology export regenerates a 24-byte static vertex stream and uint16
  indices, with a 65,535 generated-vertex limit.
- Supported collider primitives are Box, Sphere, Spheroid, Cylinder, Capsule,
  and Tapered Capsule; collider count and shape must remain unchanged.
- Custom texture export requires `texconv.exe`, the target material must
  already contain the replaced slot, and dimensions/compressed format must be
  retained.
- New content still clones an existing placeable template, `ItemInfo`, and
  recipe. Custom item icons are exported experimentally but remain blank in
  the game UI because UI texture registration is unresolved.

These are export-side constraints, not Control Center runtime evidence. The
source is the upstream project README:
https://github.com/Baik90/EnshroudedBlenderTools

| Stage | Current status | Evidence or boundary |
|---|---|---|
| File inspection and hashing | verified | `core/asset_pipeline.py` and `core/asset_service.py` |
| Dependency and ownership metadata | verified | asset manifests and template-graph planning |
| PNG/icon content route | research-only | runtime icon import evidence exists, visual presentation remains build-dependent |
| glTF/GLB/OBJ model packaging | research-only | container checks pass; Blender Tools demonstrates a RenderModel route, but Control Center's engine import is unverified |
| Material/texture graph construction | research-only | isolated material copies and existing texture-slot replacement are externally demonstrated; Control Center runtime consumption is unverified |
| Collision and LOD authoring | unsupported through verified route | no proven runtime wrapper/registration path |
| Runtime model registration | experimental | clone-only RenderModel assignment accepted, but placed rendering needs human evidence |
| BlenderTools-generated EML package | research-only | external documentation describes a concrete `render_data.bin`/Lua/resource chain; Control Center import and target-build runtime proof are still required |
| `TemplateResource` graph access | quarantined | build 1076226 metadata/GUID access did not return usable runtime resources |
| Save persistence and multiplayer authority | unverified/unsupported | no verified engine boundary for either path |

## Promotion rule

Original assets remain research-only until one fresh isolated session proves
registration, dependency resolution, visible in-game use, and rollback on the
target build. No file-format acceptance or hash record is treated as engine
import success.
