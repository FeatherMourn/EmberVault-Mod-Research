# Reusable KFC content registry helper

`kfc_content_registry.lua` packages the verified runtime route used by the bed test:

It also exposes `resource_metadata_by_type(type_name)`, a compatibility wrapper
for loader builds that support identity-only enumeration. Older builds return
`available = false` explicitly and are never forced through descriptor decoding.

- `clone_resource(donor, type_name, explicit_guid, part)` registers an independent descriptor through `game.assets.register_resource`; explicit identities are recommended for complex graph resources and registration errors are returned instead of escaping.
- `clone_icon(item_resource, texture_donor)` clones a vanilla `keen::UiTextureResource` and assigns its fresh GUID to `ItemInfo.iconImage`.
- `catalog_preview_state(item_resource)` reports the three catalog-preview
  references (`iconImage`, `iconModel`, and `iconScene`) without mutating the
  item. This is useful when a placed object works but its catalog tile is blank.
- `assign_catalog_icon(item_resource, texture_resource)` assigns a known-good
  typed `UiTextureResource` GUID to `iconImage`; it rejects missing resources
  instead of silently writing an invalid path or plain table.
- `import_png_icon(item_resource, texture_donor, png_path, format_name)` converts a PNG through EML's image/content APIs and assigns the resulting new texture resource. This remains research-only until a live visual fixture passes.
- `append_registry(registry, field, value)` adds the descriptor to a typed registry.
- `clone_recipe_set(bundle, donor_recipe_id, new_recipe_id)` clones a `FbUiBundle` recipe set and replaces its typed `HashKey32` entry.

The UI helper deliberately clones `group.sets`, not `set.entries`. The latter is a fixed-size typed array and appending to it caused an out-of-bounds error in the game.

`keen::TemplateResource` is quarantined by `resource_metadata_by_type` because
controlled testing showed that its metadata lookup blocks at runtime. Dedicated
research probes may still test it, but normal callers receive
`type_quarantined:<type>` and continue safely.

EML resolves local modules from `src/`: place the helper at `src/kfc_content_registry.lua` and load it from `src/mod.lua` with `require('kfc_content_registry')`.
