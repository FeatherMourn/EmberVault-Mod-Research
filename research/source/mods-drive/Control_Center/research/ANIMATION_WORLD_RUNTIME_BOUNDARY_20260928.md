# Animation/world runtime query boundary — 2026-09-28

## Result

The isolated probe was launched through the validated Steam research-session
launcher on build `1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z`.
It emitted:

`[CC-ANIMATION-WORLD-SCHEMA:animation_world_schema_probe_1076226] BEGIN|build=1076226|read_only=true`

The first query, for `keen::AnimationGraphResource2_0`, did not return a
`TYPE` line or an error line. The game process remained responsive but the EML
probe did not progress, so it was stopped under the bounded-probe rule. No
resource was created, assigned, registered, or saved. The probe was removed and
the stable profile passed the live-loader isolation check afterward.

## Classification

This is evidence that the current generic `get_resources_by_type` route is not
safe to batch-query this animation graph family. It is not evidence that the
underlying animation graph is impossible. The type remains research-only and
must not be queried from a stable module.

## API 1.2 follow-up

EML API 1.2 removed whole-database Lua-table preallocation from type-specific
enumeration and added an optional metadata result limit. A fresh isolated
session then completed a bounded metadata-only inventory without decoding any
payloads. It identified live GUIDs for animation graphs, actor sequences,
voxel worlds, water worlds, and world-material resources. The probe was
removed and stable-profile isolation was restored.

Evidence:
`research/probe_sessions/animation_world_metadata_runtime_evidence_20260928.json`

## Safer next step

Use the discovered GUIDs for one-resource, one-family donor studies. Continue
using `keen::actor::ActorSequenceResource` as the first payload-bearing
animation route. Keep animation-graph and world payload decoding disabled
until each donor has an isolated, bounded readback test; metadata discovery is
now safe but does not establish construction, attachment, or persistence.

Evidence session log: `H:\SteamLibrary\steamapps\common\Enshrouded\logs\2026-09-28.eml.log`

Restore report:
`research/probe_sessions/animation_world_schema_cycle_20260928_steam_restore.json`

## Water-chunk batch boundary

Offline inspection shows `keen::WaterChunkResource` has many hundreds of
content-backed parts. The shared-GUID probe therefore reads metadata from one
part only: `containsWater`, the 16-entry tile mask, and content-hash size.
Batch enumeration and content-hash materialization remain prohibited until a
separate sizing and rollback study exists.
