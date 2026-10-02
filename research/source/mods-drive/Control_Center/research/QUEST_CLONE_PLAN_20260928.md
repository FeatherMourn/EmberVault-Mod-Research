# Donor-preserving quest clone plan — 2026-09-28

## Purpose

Define the first safe quest-authoring experiment after the successful
JournalRegistry and knowledge-query schema inventories. The initial milestone
is identity and dependency readback only; it must not alter saved progression,
world knowledge, player knowledge, or multiplayer state.

## Runtime donor families

- Primary family: `keen::JournalRegistryResource`
- Observed primary resource GUID: `33701b26-ec1d-423f-8e06-49f023b91b7f`
- Quest collection: `quests`
- Runtime donor count: 168 quest records
- Supporting family: `keen::GameKnowledgeQueryResourceDb`
- Supporting family: `keen::GameKnowledgeQueryTriggerResource`

The first clone should use one bounded quest record from the JournalRegistry,
not the complete registry. A fresh probe must select and record the donor key
and a new explicit quest identity before any write is attempted.

## Dependency policy

1. Preserve the quest's `entries` array and all entry IDs until independent
   cloning of those records is proven.
2. Preserve localized name/text references initially; custom localization is a
   separate capability.
3. Preserve knowledge and completion requirements as references for the first
   identity test; do not create or modify query records in the same probe.
4. Preserve map-marker, progress-step, voiceover, item-icon, and reward
   references unchanged during the identity test.
5. Do not write to `GameKnowledgeResource`, query databases, trigger resources,
   save files, or network-owned state.
6. Do not add the clone to the live journal registry until the clone can be
   registered, read back, and proven not to mutate the donor.

## Required gates

The first quest write probe may proceed only if it can verify:

1. The donor quest is identified by a stable key and its pre-write fingerprint
   is recorded.
2. A new quest identity can be represented without reusing the donor entry ID.
3. The clone's entry count, field names, and dependency references match the
   donor.
4. The donor fingerprint is unchanged after registration.
5. The clone appears exactly once and does not replace a vanilla quest.
6. The JournalRegistry remains structurally valid.
7. No knowledge/query/trigger resource was modified.
8. The stable module starts and finishes patching without a panic.
9. The probe produces evidence and a reversible restore record.

## Explicit non-goals

This milestone does not claim:

- a new visible quest in the journal;
- custom objectives or completion logic;
- custom dialogue or localization;
- save persistence;
- rewards that are safe to grant;
- multiplayer quest authority;
- a complete quest prototype.

Those require separate readback and in-game validation gates after identity and
dependency closure are proven.

## Evidence already available

- `research/probe_sessions/journal_registry_schema_cycle_20260928_evidence.json`
- `research/probe_sessions/journal_registry_schema_cycle_20260928_restore.json`
- `research/probe_sessions/knowledge_query_schema_cycle_20260928_evidence.json`
- `research/probe_sessions/knowledge_query_schema_cycle_20260928_restore.json`

## Registry identity-clone result

The isolated identity probe registered a second JournalRegistry resource with
GUID `d5c7bb1c-398e-4cc7-8aa9-96b7d046b93f`. The donor registry retained its
original GUID and 168 quest records; the clone also exposed 168 quest records.
The clone was not attached to the live registry, save state, or knowledge
state. The stable module completed patching and the probe was rolled back.

- `research/probe_sessions/journal_registry_identity_clone_cycle_20260928_evidence.json`
- `research/probe_sessions/journal_registry_identity_clone_cycle_20260928_restore.json`

The next gate is selective quest-record cloning and dependency readback inside
an un-attached registry clone. Live journal visibility and save persistence
remain unverified.

## Standalone typed quest-resource result

The runtime accepted a sampled quest record as
`keen::JournalQuestResource` and created a standalone resource with GUID
`e7d6d3a5-9708-47c7-8c7d-78b2a3c88d41`. Readback succeeded and the original
entry identity remained present. The resource was not attached to the journal
registry or any save/knowledge state, and the probe was rolled back.

- `research/probe_sessions/journal_quest_resource_create_cycle_20260928_evidence.json`
- `research/probe_sessions/journal_quest_resource_create_cycle_20260928_restore.json`

The standalone resource also accepted a new typed `entryId` value
`3987654701` and read it back successfully. The original donor entry ID
remained unchanged, confirming donor-independent identity editing without
registry, save, or knowledge attachment.

- `research/probe_sessions/journal_quest_resource_create_cycle_20260928_edit_evidence.json`
- `research/probe_sessions/journal_quest_resource_create_cycle_20260928_edit_restore.json`

The next gate is controlled insertion of the edited standalone resource into an
unattached registry clone, followed by typed-array and donor-integrity checks.
Live journal visibility and save persistence remain unverified.

## Registry insertion boundary

The first insertion attempt is not usable: with an explicit quest-resource
GUID, `table.insert` on the cloned registry's reflected `quests` blob array
returns successfully, but the clone remains at 168 quests rather than 169.
The donor also remains at 168. A prior attempt without an explicit nested GUID
stalled during resource creation; that path is now prohibited.

This proves standalone quest creation and editing, but not registry insertion.
The typed-array append route is quarantined until a resource-aware array
replacement or registration API is identified. No live registry or save state
was changed, and the probe was restored.

- `research/probe_sessions/journal_registry_identity_clone_cycle_20260928_insert_boundary_evidence.json`
- `research/probe_sessions/journal_registry_identity_clone_cycle_20260928_insert_restore_r3.json`

## Resource-aware registry insertion result

The resource-aware route is now verified. A typed
`keen::BlobArray<keen::JournalQuestResource>` containing the original 168
records plus the edited record was created and assigned to the unattached
registry clone. The clone read back with 169 quests while the donor remained at
168. Generic `table.insert` remains unsupported for this array and must not be
used.

- `research/probe_sessions/journal_registry_identity_clone_cycle_20260928_typed_array_evidence.json`
- `research/probe_sessions/journal_registry_identity_clone_cycle_20260928_typed_array_restore.json`

The isolated live-attachment gate passed on 2026-09-28. The probe temporarily
assigned the edited typed quest array to the donor JournalRegistry and read back
169 quests (the donor began at 168); the clone registry and donor remained
distinct before attachment. This proves runtime field attachment only, not that
the edited quest appears in the visible journal or persists to a save. The probe
was removed and the stable profile restored afterward.

Evidence:

- `research/probe_sessions/journal_registry_identity_clone_cycle_20260928_live_attach_evidence.json`
- `research/probe_sessions/journal_registry_identity_clone_cycle_20260928_live_attach_restore.json`

The next gate is visible in-game journal verification and save-persistence
assessment in an isolated research profile. Stable profiles must continue to
reject this research-only module.
- `research/QUEST_SCHEMA_INVENTORY_20260928.md`

## External save-state research input

The read-only [EnshroudedSaveExplorer](https://github.com/Fab550010/EnshroudedSaveExplorer)
project provides a useful companion boundary for the next phase. Its reviewed
documentation validates JournalRegistry quest definitions and character-save
KNOW progression records, but explicitly does not characterize world saves or
write save files. That makes it suitable for observing progression evidence,
not for proving that a newly attached runtime quest is visible, completable,
or multiplayer-safe.

Use it in the following order:

1. Capture the active character save generation through `characters-index`
   before the isolated runtime session.
2. Record a read-only KNOW snapshot before and after any intentionally bounded
   quest interaction.
3. Compare only the expected knowledge IDs and preserve the original save.
4. Treat mismatched or shared-world results as inconclusive until host/client
   behavior is separately tested.

The comparison and limitations are recorded in
`research/EXTERNAL_SAVE_EXPLORER_COMPARISON_20260928.md`. This does not change
the current classification: visible journal behavior, save persistence, and
multiplayer authority remain unverified.
