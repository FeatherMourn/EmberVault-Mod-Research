# ActorSequenceResource donor-preserving clone plan — 2026-09-28

## Purpose

Define the next controlled step toward custom AI behavior: prove that an existing
`keen::actor::ActorSequenceResource` can be registered as a separate resource
with a new identity, while preserving the donor and avoiding any live behavior
attachment.

This is an identity-and-readback experiment, not yet a new enemy attack or a
claim of general AI authoring support.

## Donor and planned clone

- Donor GUID: `a837f190-d163-4ef5-a48e-3ea7caac7296`
- Resource type: `keen::actor::ActorSequenceResource`
- Planned clone GUID: `c8f7a8a3-6f6f-4ae9-b15e-30fd2c5c7e11`
- Donor evidence: `research/probe_sessions/actor_sequence_event_graph_cycle_20260928/evidence.json`
- Successful identity-clone evidence: `research/probe_sessions/actor_sequence_identity_clone_cycle_20260928/evidence.json`
- Successful isolated attack-attachment evidence: `research/probe_sessions/actor_sequence_identity_clone_cycle_20260928/attachment_evidence.json`
- Restore evidence: `research/probe_sessions/actor_sequence_identity_clone_cycle_20260928/restore.json`
- Attack-attachment restore evidence: `research/probe_sessions/actor_sequence_identity_clone_cycle_20260928/restore_attachment.json`
- Donor event graph: 41 traversed events in the resolved runtime sample

The planned GUID is reserved for the probe and must not replace, mutate, or be
attached in place of the donor.

## Registration method

Use the validated helper primitive:

```lua
local clone, err = kfc.clone_resource(
    donor,
    'keen::actor::ActorSequenceResource',
    'c8f7a8a3-6f6f-4ae9-b15e-30fd2c5c7e11',
    0
)
```

The helper performs guarded `game.assets.register_resource` registration and
returns either the registered resource or a descriptive error. The probe must
fail closed if the donor data, type, GUID, or registration result is invalid.

## Dependency policy for the first clone

1. Preserve the complete donor payload, including all 41 event records.
2. Preserve the 17 directly mapped external dependencies discovered in the
   dependency-closure research: the donor ActorSequenceResource, its mapped
   ImpactProgram, eight SoundContainerResource entries, four VfxResource
   entries, and three VfxMeshData entries.
3. Reuse unresolved event-local GUIDs and IDs unchanged for this first clone;
   do not invent replacements during the identity test.
4. Do not modify event types, timing, animation names, impact data, sound,
   visual effects, or actor references in this phase.
5. The isolated attachment test may change one donor attack reference only;
   it must not alter the donor sequence payload or any spawn, quest, or
   multiplayer-authority path.

## Required verification gates

The probe is successful only when all gates pass:

1. The donor still resolves by its original GUID before and after registration.
2. A pre-registration donor fingerprint and post-registration donor
   fingerprint match.
3. The clone appears exactly once under the planned GUID.
4. The clone reports resource type
   `keen::actor::ActorSequenceResource` and `resourceId` equal to the planned
   GUID.
5. The clone's `resourceId` equals the planned GUID and its `subSequences`
   count matches the donor.
6. Every traversed clone event has the same order and event type as the donor.
7. Exactly one isolated attack reference changes from donor GUID to clone GUID.
8. No existing resource, registry entry, donor payload, or stable mod output is
   overwritten.
9. The normal stable mod starts and completes without a loader panic.
10. The probe writes evidence and a restore record before the process exits.

Any failed gate stops the experiment and leaves the clone unattached.

## Rollback and recovery

- Stop the game before changing the live probe or loader runtime.
- Keep the existing stable DLL and stable mod backup available.
- Remove only the staged probe after the run; restore the prior DLL if a rebuilt
  runtime was used.
- Confirm the live loader with:

  ```text
  python tools/verify_live_loader.py "H:\\SteamLibrary\\steamapps\\common\\Enshrouded" --require-isolated --expected-build "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z"
  ```

- A rollback is complete only when the live profile reports one stable mod,
  zero invalid folders, compatible build, and `status: ready`.

## Explicit non-goals

This milestone does not establish:

- custom AI behavior attached to an enemy;
- a new enemy archetype or spawnable creature;
- new quest progression;
- original animation, mesh, sound, or VFX authoring;
- world generation or multiplayer authority support.

Those capabilities remain separate research milestones after clone identity,
dependency closure, safe attachment, and visible behavior verification are
proven.
