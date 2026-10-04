# Building data ingestion — revision 1076226

- Topic: data formats / KFC / building catalog
- Status: confirmed for the recorded bundle and executable inputs
- Confidence: high for recorded counts and provenance; medium for portability to later builds
- Build: revision `1076226`

## Supported conclusion

The ingestion workflow extracts nested archives without modifying the original bundle, records bundle and nested-archive hashes, preserves unresolved references, and produces normalized relationships for ItemInfo, ItemRegistry, recipes, blueprints, terrain, buildings, materials, feedback resources, and snap rules.

The recorded rebuild contains 3,616 ItemInfo identities, 3,527 resolved ItemRegistry links, 1,955 recipes, 5,724 recipe inputs, 1,943 recipe outputs, 141 blueprint records, 112 terrain configurations, 86 building configurations, 258 material-layer records, 249 MaterialFeedback resources, and 31 normalized snap rules. These counts are evidence for the named input bundle, not universal game totals.

## Evidence and provenance

- `../source/mods-drive/Architect_Mod/Code_History/CODE-0037-working/architect_toolkit/docs/research/BuildingKfcIngestion-1076226.md`
- `../source/mods-drive/Architect_Mod/Code_History/CODE-0037-working/architect_toolkit/tools/ArchitectDataIndex.md`
- Related builder and validation artifacts under the same `architect_toolkit` tree

## Modding implications

The catalog is useful for identity lookup, recipe/building relationships, and offline planning. It does not by itself prove that a runtime object can be safely mutated or that a source field is accepted by the live game.

## Open questions

- Which normalized fields remain stable across game updates?
- Which unresolved references are expected optional data versus extraction gaps?
- Can the catalog drive a repeatable offline mod-planning or validation tool?
