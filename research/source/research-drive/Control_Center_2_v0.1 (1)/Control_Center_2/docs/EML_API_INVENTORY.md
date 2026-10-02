# CC2 EML API inventory

Installed source files (read-only): `H:\SteamLibrary\steamapps\common\Enshrouded\.cache\lua`.

| File | SHA-256 | Bytes | Timestamp |
|---|---|---:|---|
| base.lua | `98847ab86a8d73a18ae2b78c53fb73db0c406e776d426d26e36048cb4142c1d0` | 96560 | 2026-09-10 13:38:53 |
| types.lua | `ff345a2eeaf939ed13599ce25c4b8cc24aaabe8e36dfcd5ad255533e4637a1c81` | 1295957 | 2026-09-10 13:38:53 |

`base.lua` declares `get_resource(guid,type,part?)`, `get_resource_parts(guid,type)`, `get_resources_by_type(type)`, `get_all_resources()`, `get_resource_types()`, `get_content(guid)`, and resource/content creation functions. Creation is logged only and never called by CC2.

It defines `Guid` as a UUID string and `GuidHelper` with `NONE`, `from_content_hash`, `to_content_hash`, and `hash`.

`types.lua` declares `keen.ItemInfo` (including `itemId`, `objectId`, name/description, `iconImage`, `iconModel`, `debugName`), `keen.ItemRegistryResource` (`itemRefs`, `itemTags`, `weaponCategories`, `dbgNames`), `keen.ItemKnowledgeResource` (`knowledgeArray`), `keen.RecipeRegistryResource` (`inputCategories`, `recipes`), `keen.RecipeInfo` (recipe/workshop/input/output/knowledge fields), and `keen.WorkshopRegistryResource` (`npcs`, `workshops`, `craftingProps`).

These are installed declarations, not runtime observations. They provide no EML package version or game build.
