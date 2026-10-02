# KFC Runtime Registration Loader — Build 1076226

## Verified capability

The EML loader can create a new `keen::ItemInfo` resource and register a new
item and recipe at runtime when all positional registry data is updated:

- create the cloned `ItemInfo` with `game.assets.create_resource()`;
- assign a new `itemId`, `objectId`, and debug name;
- append the cloned resource to `ItemRegistryResource.itemRefs`;
- append the matching name to `ItemRegistryResource.dbgNames`;
- append the cloned recipe to `RecipeRegistryResource.recipes`;
- clone the `ItemKnowledgeResource` record;
- construct a typed `keen::HashKey32` through `create_resource()` for UI links;
- assign that typed value into an existing `FbUiBundle` recipe slot.

The live log verified `items=3520->3521`, `recipes=1954->1955`,
`dbgNames=3521`, and `UI_LINKS=1`.

## Current engine limit

`FbUiBundle` recipe entry arrays are fixed-length. Direct assignment can replace
an existing slot, but assigning index 10 to the nine-entry furniture set fails
with an out-of-bounds error. `table.insert()` does not resize the native array.

The loader therefore supports a working replacement mode. A separate new menu
slot requires an exposed native array-resize/catalog-registration API or a KFC
writer that can rebuild the typed array descriptor and resource index.

## Artifacts

- Runtime loader: `research/probes/bed_clone_injection_1076226/src/mod.lua`
- Offline archive inspector: `research/tools/kfc_index_inspector.py`
- Working archive copy: `H:\Enshrouded_KFC_WorkingCopy_20260926`
- Live mod folder: `H:\SteamLibrary\steamapps\common\Enshrouded\mods\bed_clone_injection_1076226`

The live game archive itself has not been overwritten.
