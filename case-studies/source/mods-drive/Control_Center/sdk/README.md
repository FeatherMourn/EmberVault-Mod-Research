# Enshrouded Control Center Developer SDK

The SDK is the supported authoring surface for EML/KFC runtime content. Keep
custom content in a separate mod folder and let the Control Center validate and
package it before activation.

## Stable contract

- `game.assets.register_resource(value, type, guid, part)` registers a runtime resource.
- `kfc.clone_resource(donor, type_name)` creates an independent resource clone.
- `kfc.append_registry(registry, field, value)` appends to a dynamic registry.
- `kfc.clone_recipe_set(bundle, donor_recipe_id, new_recipe_id)` safely clones a
  UI recipe set. Do not append to fixed-size `set.entries` arrays.

The helper is packaged beside each generated module at
`src/kfc_content_registry.lua`. Modules should declare required capabilities in
`mod.json` and remain `research-only` until their donor schemas are validated.

## Workflow

1. Generate a content project from Content Studio.
2. Inspect and validate donor resources.
3. Add Lua changes under `src/mod.lua`.
4. Validate, smoke-test, and export the package.
5. Review the dry-run deployment before enabling it in a profile.

See [bed_clone.lua](examples/bed_clone.lua) for the verified furniture pattern.
