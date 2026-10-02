# EML Resource Registration Upgrade

## Finding

The existing Lua API already writes newly-created descriptors through `game.assets.create_resource(value, type, guid, part)`, but its discovery functions only enumerate the original KFC index. Newly registered resources therefore exist in the patch writer and Lua cache while remaining invisible to `get_resources_by_type()` and `get_all_resources()`.

## Source change

The local EML source fork adds:

- `game.assets.register_resource(...)` as an explicit alias for descriptor registration;
- newly registered resources to `get_resources_by_type()`;
- newly registered resources to `get_all_resources()`;
- duplicate suppression when a resource is already in the original KFC index.

Source: `H:\enshroudedresearch\external\kfc-parser-source\crates\mod-loader-lua\src\env\game\assets.rs`

## Verification

`cargo check -p mod-loader-lua` completed successfully after the change. The existing warnings are upstream lifetime/dead-code warnings; no new errors were introduced.

The full patched `dinput8.dll` proxy was then built and installed with a backup. The runtime probe changed from `INDEXED_ITEMS_AFTER_CREATE|3609` on the old loader to `INDEXED_ITEMS_AFTER_CREATE|3610` on the upgraded loader, while the custom item registration continued to report `itemId=3987654321` and `recipeId=3987654322`.

A direct lookup test now reports `DISCOVERED_CLONE|true` for the newly created `ItemInfo`, proving that a mod can retrieve a fresh descriptor through EML after registration.

## Why this matters

This makes EML’s resource layer behave like a live registry instead of a read-only view of the original archive. It does not by itself solve every game-side catalog constraint: UI arrays, recipe registries, knowledge gates, and content dependencies still require valid typed descriptors. It does provide the missing loader primitive needed for mods to register and discover new KFC resources consistently.
