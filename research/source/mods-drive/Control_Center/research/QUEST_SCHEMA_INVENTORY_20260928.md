# Quest and progression schema inventory — 2026-09-28

## Finding

The extracted KFC does not expose a directory named `QuestResource` or
`MissionResource`. Quest/progression data is represented through broader
resource families instead of one obvious quest type.

## Candidate resource families

| KFC family | Observed top-level fields | Initial interpretation |
|---|---|---|
| `keen::JournalRegistryResource` | `quests`, `collections`, `itemSetCategories`, `itemSetRewards` | Primary quest/journal donor candidate |
| `keen::GameKnowledgeResource` | `worldKnowledge`, `playerKnowledge`, `achievements`, `skillPoints`, `flagKnowledgePatch` | Save/progression state boundary candidate |
| `keen::GameKnowledgeQueryResourceDb` | `queries`, `runtimeQueries`, `queriedItems`, query indexes | Query/objective trigger candidate |
| `keen::GameKnowledgeQueryTriggerResource` | `worldQueries`, `playerQueries`, event-based world/player queries | Event-driven progression candidate |
| `keen::NpcCollection` | `npcs` | NPC linkage candidate |
| `keen::AchievementDefinitionResource` | `achievements` | Reward/achievement boundary candidate |

## Runtime evidence

The isolated probe verified one runtime `keen::JournalRegistryResource` with
168 quest records. Each sampled quest exposed 11 fields, including:

- `entryId`, localized-name/text references, and referenced document;
- priority, tutorial flag, source, type, and unlock policy;
- entry arrays containing knowledge and completion requirements;
- map-marker references, progress-step requirements, voiceover, and rewards.

The normal stable module continued afterward and applied 1,910 patches without
a panic.

Evidence and rollback records:

- `research/probe_sessions/journal_registry_schema_cycle_20260928_evidence.json`
- `research/probe_sessions/journal_registry_schema_cycle_20260928_restore.json`

## Evidence source

Offline samples were inspected under
`H:\Enshrouded_KFC_Extracted_20260926` on build `1076226`. The sample files
reported these `$type` values and top-level field sets; this is schema
discovery only and is not runtime proof.

## Safe next probe

Create an isolated, read-only runtime probe for
`keen::JournalRegistryResource` that records:

1. resource count and donor GUIDs;
2. bounded `quests` collection count;
3. shallow quest field names and value types;
4. references to knowledge queries, NPCs, rewards, dialogue, and world flags;
5. no assignments, registration, save writes, or persistence changes.

If the reflected resource is opaque or causes a panic, quarantine the family
and retain the offline schema as the boundary evidence. Do not attempt quest
mutation until the complete donor graph and save-authority boundary are known.

## Current classification

Quest systems remain `research-only`. The runtime inventory improves donor
discovery but does not establish custom objectives, triggers, rewards, save
persistence, multiplayer authority, or a working quest prototype.

The follow-up knowledge probe also verified one
`keen::GameKnowledgeQueryResourceDb` and one
`keen::GameKnowledgeQueryTriggerResource`. Their reflected data includes
indexed query records, named knowledge actions, player/world query flags,
comparison operators, unlock knowledge, and event-based player/world trigger
collections. Evidence and rollback are recorded at:

- `research/probe_sessions/knowledge_query_schema_cycle_20260928_evidence.json`
- `research/probe_sessions/knowledge_query_schema_cycle_20260928_restore.json`
