# KFC static findings — scoped research notes

Sources: copies of selected archives in the user's read-only `ENSHROUDED KFC FILES`; original Drive ZIPs not modified. The catalog stores SHA-256, member and resource GUID provenance. The current derived catalog indexes 11 selected archives. The project previously located 25 relevant archives, but the other 14 were downloaded for further analysis and are **not** yet fully indexed in this build. Do not confuse indexed archive counts with all KFC source coverage.

## Observed static relationships

- `ItemInfo` exports contain individual item GUIDs, `itemId`, debug category, localization references and icon/model references where present.
- `ItemRegistryResource` links existing item GUIDs; `RecipeRegistryResource` has recipe GUID/ID, workshop reference, inputs and outputs. `ItemKnowledgeResource` and `WorkshopRegistryResource` provide further links. These are **static field observations**, not proof of corresponding EML mutable Lua layouts.
- Initial snapshot: **3,609 ItemInfo**, **3,520 registered items**, **1,954 recipes**, **4,017 item-knowledge entries**, **46 workshops**. 89 `ItemInfo` entries are not in the observed registry; zero registry GUIDs lack matching ItemInfo. The catalog's current reference checks report zero unresolved item-bearing recipe inputs/outputs among the references counted; this does **not** prove runtime validity or complete coverage of category-only ingredients.
- The original Control Center importer uses hard-coded recipe *positions* and mostly mutates existing recipe inputs/output counts and vanilla item stack properties. Its custom names, meshes, textures and effects are not thereby independently registered. Multiple modules can select overlapping positions. This is observed in source; no in-game test has been performed here.

## Status

**PROVEN (static):** these fields/relationships occur in this specific archive snapshot. **INFERRED:** a complete independent custom item probably needs coordinated item identity, registration, recipes, unlock knowledge, localization and UI/visual references. **UNSOLVED:** which of those are strictly required at runtime, actual EML callable signatures, registration timing, safe new itemId generation, network authority and save behavior. **NEXT TEST:** observe installed EML APIs with isolated probe, then a separately reviewed single-item creation experiment; never assume a new UUID alone makes a complete usable item.

### Do not infer from the catalog

File modification dates do not prove game build number. Localized display strings are not provided by a localization GUID alone. An icon or mesh GUID in ItemInfo is a reference, not evidence that custom binary import exists. A plan saved by CC2 does not modify or create an Enshrouded resource.
