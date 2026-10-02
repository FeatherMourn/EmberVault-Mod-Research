# AI event dependency closure — 2026-09-28

## Donor

- Actor sequence: `a837f190-d163-4ef5-a48e-3ea7caac7296`
- Name: `Enemy_Fogger_Heavy_Attack03_Chain_3hit_more_turn_events`
- Runtime events: 41
- Runtime resource family: `keen::actor::ActorSequenceResource`
- Runtime resource inventory: 2,202 entries

## Event graph

The runtime graph exposes animation, ability, audio, VFX, noise, impact, and
camera-shake events. The event payloads are mapped variants with readable
`.type` and `.value` fields. The event inventory was completed without a loader
panic, and the stable Control Center mod applied 1,911 patches in the same
session.

## Offline dependency mapping

The donor contains 45 unique GUID values. The extracted KFC working copy maps
17 of them directly to known resource archives:

- 1 `ActorSequenceResource`
- 1 `ImpactProgram`
- 8 `SoundContainerResource`
- 4 `VfxResource`
- 3 `VfxMeshData`

The remaining GUIDs are embedded event identifiers, animation names, entity
tags, impact configuration/object identifiers, or references whose owning
resource family still needs identification. They must not be treated as safe
to rewrite merely because they are syntactically GUIDs.

## Runtime evidence

- `research/probe_sessions/actor_sequence_guid_lookup_cycle_20260928/evidence.json`
- `research/probe_sessions/actor_sequence_event_graph_cycle_20260928/evidence.json`

## Mutation gate

The closure is sufficient to plan a donor-preserving read/clone experiment,
but not yet sufficient for a production AI clone. Before mutation, the tool
must either resolve or deliberately preserve every event dependency, register
the cloned sequence under a new identity, and prove rollback after a fresh
runtime session.
