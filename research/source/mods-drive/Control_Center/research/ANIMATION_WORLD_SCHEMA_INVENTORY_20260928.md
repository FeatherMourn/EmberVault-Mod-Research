# Animation and world-generation schema inventory

## Scope

This is a read-only inventory of the build pinned by the current EML profile:

`1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z`

Source: `H:\SteamLibrary\steamapps\common\Enshrouded\.cache\types.json`.
The inventory proves that the type registry exposes schema names; it does not
prove that Lua can safely construct, register, attach, or persist these graphs.

## Animation families observed

- `keen::Animation` (type 110): animation node, hierarchy, model hints, frame
  range, loop mode, root-motion/export flags.
- `keen::AnimationSequenceContainer` (type 121): sequence collection.
- `keen::animationgraph::AnimationGraphInfo` (type 193): graph id,
  post-process id, nodes, inputs, overlays, and model hierarchy.
- `keen::anim_graph::tool_graph::AnimationGraph2_0` (type 369): post-process
  graphs, cloth collider reference, model override, and gender mapping.
- `keen::anim_graph::runtime_graph::AnimationGraphResource2_0` (type 457):
  runtime animation graph resource family.
- `keen::anim_graph::runtime_graph::StateMachineNodeDefinition` (type 407)
  and `StateMachineTransitionNodeDefinition` (type 409): state-machine and
  transition structures with conditions, priorities, root-motion, and event
  modes.
- `keen::actor::SetAnimationEvent` (type 1644): actor event-level animation
  selection and retrigger controls.

## World-related families observed

- `keen::VoxelWorldResource` (type 6904): voxel-world resource family.
- `keen::VoxelWorldChunkResource` (type 6906): chunk-level world resource.
- `keen::WaterWorldResource` (type 6908): water-world resource family.
- `keen::WorldMaterialBlending2Resource` (type 6278) and
  `keen::SimpleWorldMaterialResource` (type 5856): world-material graphs.
- `keen::WorldKnowledgeObjectResource` (type 4886): world-knowledge resource
  family that may participate in world-state generation or discovery.
- `keen::GameKnowledgeGenerationScope` (type 3862): knowledge-generation scope
  rather than a procedural world generator.

## Current classification

The registry contains animation graphs, state-machine definitions, and world
resource schemas, but this inventory found no demonstrated general-purpose
world-generation resource or safe EML construction route. Animation is a
candidate for bounded donor-read and clone probes; world generation remains
research-only until a concrete donor resource, registration path, and runtime
attachment point are identified.

## Next bounded gates

1. Bounded metadata enumeration is complete under EML API 1.2; preserve its
   build-pinned evidence and exact qualified type names.
2. Use the discovered animation-graph donor
   `0022fed6-0380-4125-be31-ba8b5fdcbfcd` for a single-resource payload and
   dependency-boundary probe.
3. Perform an isolated identity clone/readback probe only if the resource is
   returned through the EML asset API.
4. Use voxel-world donor `022bd475-089a-43b8-b49a-2bcf2f0cd84f` only in a
   read-only single-resource probe; do not write world data or touch a saved
   world until registration and persistence behavior are understood.
5. Keep both capabilities research-only until visible runtime behavior and
   rollback evidence exist.

## Voxel-world single-donor payload result

The build-pinned EML API 1.3 probe safely resolved
`022bd475-089a-43b8-b49a-2bcf2f0cd84f` as a
`keen::VoxelWorldResource` and decoded its payload. The selected donor is a
256 x 16 x 256 solid resource with 256 material entries and seven voxel
levels. The first level has an 8 x 8 tile size, a 1 x 1 tile count, and one
tile. Runtime values exactly matched the offline archive.

This result proves only bounded resource discovery and payload decoding. The
probe did not create, register, clone, mutate, attach, stream, or persist world
data. It did not access a saved world. The game was stopped, the probe was
uninstalled, and stable-only loader isolation was restored. World generation
therefore remains research-only.

Evidence:
`research/probe_sessions/voxel_world_single_donor_runtime_evidence_20260928.json`

The next safe gate is dependency and ownership mapping for the tile hashes and
material table. No identity clone should be attempted until those boundaries
and the resource-registration consequences are understood.

## Voxel-world dependency and material-table result

The reusable offline mapper classified all 135 exported voxel-world records:
130 unique world GUIDs, 130 solid records, five fog records, ten records that
share a GUID with an exported scene, and 125 standalone records. Across the
archive there are 19,861 unique `ContentHash` references representing about
4.87 GB of binary content and 198 unique non-null entries in the fixed material
table. `ContentHash` is a binary-content identity, not a typed resource GUID.

A bounded API 1.3 metadata sample then tested 12 entries from a scene-owned
world's material table. Seven resolved, all as `keen::VoxelWorldResource`; five
had no registered resource identity. None resolved as a material resource type.
The table therefore cannot safely be interpreted as an ordinary list of
material-resource dependencies. No payload, world, or save access occurred.

Evidence:

- `research/VOXEL_WORLD_DEPENDENCY_MAP_1076226.json`
- `research/probe_sessions/voxel_material_guid_type_runtime_evidence_20260928.json`

The next safe gate is to classify the complete 198-entry table through metadata
only and inspect the four small scene-owned solid/fog pairs. Resource cloning
and registration remain prohibited until the semantic role of unresolved
entries and binary-content ownership is known.

The complete metadata-only classification is now finished. Of all 198 unique
non-null table entries, 125 resolve one-to-one as the 125 standalone
`keen::VoxelWorldResource` records and 73 have no registered resource identity.
No other resource type appears. Exact sorted identity-set hashes are retained
in the evidence so the classification cannot silently drift. This supports a
palette/index relationship hypothesis, but does not yet prove how those 125
standalone voxel resources are consumed by a scene-owned world.

Evidence:
`research/probe_sessions/voxel_material_full_metadata_runtime_evidence_20260928.json`

The next safe gate is a read-only paired inspection of one small scene's solid
and fog world records plus its matching `SceneResource`. Cloning, registration,
attachment, binary-content replacement, and save access remain prohibited.

The paired runtime inspection is complete for shared GUID
`36234b22-85f2-4001-ac56-002b379d0d88`. EML API 1.3 decoded the scene at part
0, the solid voxel world at part 0, and the fog voxel world at part 1. All
bounded fields matched their offline exports: the scene has five nodes, one
camera, four VFX entries, and a 1 x 1 entity grid; each voxel world has seven
levels and ten tile references. This proves the shared-GUID/part grouping, but
not runtime attachment, loading ownership, or world-generation semantics.

Evidence:
`research/probe_sessions/scene_voxel_pair_runtime_evidence_20260928.json`

The next safe gate is metadata-only discovery of same-GUID chunk/resource
families and their part ranges. Binary `ContentHash` reads, scene attachment,
world mutation, and save access remain prohibited.

The same-GUID family map is now verified. The tested scene exposes scene part
0; voxel-world parts 0 and 1; fog, water, water-chunk, fog-mapping parts 0;
scene-entity parts 0 and 1; and render-model parts 0 and 1. No
`VoxelWorldChunkResource` or render-model-grid record is registered for this
GUID. This is an ownership/part-range map only; it does not prove load order,
payload ownership, or runtime attachment.

Evidence:
`research/probe_sessions/scene_resource_family_metadata_runtime_evidence_20260928.json`

The next safe gate is a bounded payload read of one non-voxel companion
resource only if its offline schema and binary dependencies are small. Voxel
chunk/content payloads and all mutation or save paths remain prohibited.

That gate is complete for `keen::WaterWorldResource`, part 0. Its runtime
payload matched the offline export: a 1 x 1 tile grid, origin 0/0/0, and a
256-entry behavior table. The associated `WaterChunkResource` content hash was
not read, and no water-world mutation or attachment was attempted.

Evidence:
`research/probe_sessions/water_world_single_donor_runtime_evidence_20260928.json`

The next safe gate is offline dependency sizing for `FogVoxelMappingResource`
or another small companion. Binary voxel/water chunk content, registration,
world mutation, and save access remain prohibited.

## Single-donor payload result

The isolated API 1.2 probe resolved donor
`0022fed6-0380-4125-be31-ba8b5fdcbfcd`, read its typed payload, and confirmed
hierarchy `f46c0d0d-2c8c-4189-8893-edb74832529c`, 108 node definitions, 36
slot/bone mappings, 26 used input IDs, and root node `3143804083`. No resource,
animation, entity, world, or save attachment occurred. The probe was removed
and stable-profile isolation was restored.

Evidence:
`research/probe_sessions/animation_graph_single_donor_runtime_evidence_20260928.json`

The bounded dependency traversal gate is complete: all 108 node definitions
were classified into seven concrete node types and 32 unique dependency GUIDs
were mapped by role. The authoritative evidence is
`probe_sessions/animation_graph_dependency_runtime_evidence_20260928.json`.
Exact resource-type resolution is also complete through EML API 1.3: the 32
GUIDs resolve to 42 identities across six resource types. Nine GUIDs are
intentionally multi-typed. A donor-preserving identity clone is now verified
with a unique GUID, 108-node parity, and complete 32-dependency parity. The
clone was then attached in isolation to `NPC_Workshop_Hunter01` through
`keen::NpcCollection.uiRendering.animationGraph2`, without touching the
quarantined template or entity/world/save state. The next gate is controlled
visible observation of the Hunter. A separate bounded clone edit already
reroutes the `idle` state from pose `2585692075` to the existing same-graph
`idle_Var_02` pose `3890759935`; its structural edit and owner attachment are
verified, but its visible behavior is deliberately not yet claimed.
