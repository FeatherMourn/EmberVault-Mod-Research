# EnshroudedSaveExplorer research comparison

Date: 2026-09-28  
Source: [Fab550010/EnshroudedSaveExplorer](https://github.com/Fab550010/EnshroudedSaveExplorer)  
Reviewed revision: `1b04361dbd46937d8c6e919e9e95618c01dd393b`

## Executive finding

EnshroudedSaveExplorer is a valuable read-only research reference for save-state and quest/progression analysis. It does not provide runtime engine authority, asset injection, world-save writing, multiplayer replication, or a replacement for EML. Its strongest immediate value is helping Control Center distinguish persistent player knowledge from runtime resource definitions and identify safe evidence paths for future quest and persistence tooling.

## What the project validates

- KFC3 resource indexing and extraction from `enshrouded.kfc` plus `enshrouded.kfc_resources` using resource keys rather than build-specific indexes.
- Targeted extraction of `JournalRegistryResource`, including quest IDs, quest source/type, journal entries, requirements, rewards, and progression-step metadata.
- KSC1 character-save containers, Zstandard-compressed blobs, rolling-save selection through `characters-index`, and OwnerID associations.
- KNOW progression data as a generic persistent knowledge table covering quests, recipes, items, events, and progress markers.
- Practical quest interpretation rules: PlayerQuest and WorldQuest completion indicators are stronger than Auto-quest indicators, while Auto quests cannot generally establish personal versus inherited/world origin.
- Localization and Steam-save discovery patterns, with explicit warnings that undocumented formats and build-specific offsets can change.

## What this adds to our project

1. **Quest research becomes concrete.** We can build a read-only Control Center research view that maps JournalRegistry quest definitions to observed save knowledge, without claiming that it creates or runs quests.
2. **Persistence validation can improve.** The save index and rolling-generation rules provide a safer way to identify the active character save before comparing before/after gameplay evidence.
3. **Recipe and progression analysis can expand.** KNOW is a candidate source for discovering persistent progression relationships that are not visible in the runtime catalog alone.
4. **Resource indexing aligns with our EML direction.** Resource-key lookup and content-based file identification reinforce our existing rule to avoid hardcoded physical indexes and build-specific assumptions.
5. **Multiplayer analysis gains a boundary.** The project’s quest caveat—shared-server state can differ from personal state—supports keeping multiplayer authority and replication marked unresolved until peer-visible runtime evidence exists.

## Important limits

- The project intentionally reads saves; it does not intentionally modify them.
- Its published document says full world-save format is not characterized. Therefore it does not yet prove that buildings, placed furniture, terrain, chests, or world quest state can be safely edited.
- Save-file knowledge is post-session state, not live engine authority. It cannot by itself add new resource graphs, register new runtime objects, provide new AI/animation/interactions, or implement server replication.
- JournalRegistry definitions describe existing game data. They do not demonstrate that arbitrary new quest records can be safely injected.
- The source warns that undocumented formats, offsets, hashes, and schemas may change with updates.

## Recommended integration path

### Safe now: research-only

- Add a read-only Save Research adapter to Control Center.
- Discover the active character save through `characters-index`.
- Parse and display quest/lore/progression evidence with origin labels: `definition`, `character knowledge`, `runtime observation`, or `unknown`.
- Hash and archive before/after save snapshots; never write to live saves in the first implementation.
- Use the repository’s KFC3 resource-key approach to improve cross-build resource inventory and drift diagnostics.

### Requires controlled testing

- Compare a controlled single-player action against KNOW changes.
- Compare a hosted multiplayer action against host and client saves separately.
- Determine whether placed furniture or world changes appear in accessible world-save structures.
- Test rollback using copied saves only, with the game closed and a verified backup.

### Still requires EML/engine support

- New runtime quest logic, interactions, AI, animation, world generation, asset import, or multiplayer authority.
- Safe world-save mutation or new world-entity creation.
- Any claim that a save edit is multiplayer-safe or server-authoritative.

## Decision

Use EnshroudedSaveExplorer as a read-only companion research source and future persistence-inspection component. Do not merge its parser wholesale into the runtime mod loader, and do not promote save-derived findings to verified mod capabilities without fresh isolated in-game evidence.

