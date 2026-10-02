# Asset Publication Findings — build 1076226

## Confirmed

- `game.assets.create_resource(value, type)` creates a Lua-visible resource and a new GUID.
- The cloned `ItemInfo` can be appended to `ItemRegistryResource.itemRefs`.
- The cloned recipe can be appended to `RecipeRegistryResource.recipes`.
- The furniture recipe tree can accept a copied native menu entry.
- The cloned knowledge record can be appended to `ItemKnowledgeResource.knowledgeArray`.

## Runtime result

The bed clone used item ID `3987654321` and recipe ID `3987654322`.

The injection log reported successful temporary registration, but immediately after `create_resource`:

```text
indexed ItemInfo count = 3609
normal indexed ItemInfo count = 3609
```

The clone therefore did not enter the indexed `ItemInfo` asset collection consumed by the game catalog. It was only present in the Lua-side object and manually patched arrays.

## API boundary

The build-matched EML API definitions expose:

- `get_resource_types`
- `get_all_resources`
- `get_resources_by_type`
- `get_resource`
- `create_resource`
- `get_content`
- `get_all_contents`
- `create_content`

They do not expose a resource publish, register, reindex, reload, or catalog-invalidation operation.

## Conclusion

New content cannot currently be presented as a confirmed EML-only feature. The next viable research path is outside ordinary resource mutation: identify whether the native loader has an undocumented publication boundary or whether content must be supplied as an external asset/content package before EML startup.
