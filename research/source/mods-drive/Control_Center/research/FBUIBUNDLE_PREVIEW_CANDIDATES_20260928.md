# FbUiBundle preview candidates — build 1076226

The KFC inventory shows that `keen::FbUiBundle` is a large resource with
top-level `icons`, `menu`, and `itemSlot` containers. Its `icon` attribute is
bundle metadata, not proof of an item-catalog tile reference. By contrast,
`show_picker_preview` is an attribute on the ItemInfo reflected type, so it is
not itself a field that can be assigned on a cloned `FbUiBundle`.

This distinction removes a misleading candidate from the next live test. The
remaining UI-side investigation should inspect the typed contents of the
`icons`, `menu`, and `itemSlot` containers, especially the cloned recipe-set
entry and any references reachable from those containers.

Current evidence does not prove that any of these fields can be modified from
Lua or that they control the Carpenter catalog tile. They remain research-only
and must be tested with a fresh session and screenshot verdict.

Source: `research/KFC_Tuning_Field_Inventory_1076226.json`, family
`FbUiBundle`, reflected type `keen::FbUiBundle`.

## Runtime structure result

The read-only probe `fb_ui_bundle_structure_probe_20260928` ran successfully
on the target build. Lua exposed `icons`, `menu`, `itemSlot`,
`menu.crafting`, `menu.crafting.recipes`, and
`menu.crafting.recipes.trees` as `userdata`. The probe completed without
mutation or panic. This confirms the containers are reachable, but ordinary
Lua table iteration cannot inspect their typed contents; a follow-up must use
the loader's typed-resource accessors or targeted field reads.
