# UI icon resource schema — build 1076226

## Verified findings

`keen::ItemInfo.iconImage` is a typed resource-reference field, not a path or localization key.

| Field | Type index | Meaning |
|---|---:|---|
| `keen::ItemInfo.iconImage` | 1924 | typed reference slot for an icon texture |
| `keen::ItemInfo.iconModel` | 104 | 3D/model fallback when `iconImage` is absent |
| `keen::ItemInfo.iconScene` | 3854 | scene fallback when `iconImage` is absent |
| `keen::UiTextureResource` | 4677 | texture resource wrapper |
| `keen::ds::UiTextureResource` | 11795 | data-side reflected variant |

The reflected `UiTextureResource` contains:

- `data` — type 519, marked `ContentCategory::UiTexture`;
- `debugName`;
- `size`;
- `type` and `format`;
- `levelCount`;
- `isTiled`.

The `ItemInfo` reflection marks `iconModel`, `iconScene`, and icon render settings as disabled when `iconImage` is present. The existing bed fixture has `iconImage = null` and therefore uses the donor model/scene route.

## Implementation consequence

The loader should support two icon modes:

1. **Donor icon mode (safe first target):** clone or reference a known-good `UiTextureResource` through the exact typed reference used by `iconImage`.
2. **Imported icon mode (research target):** construct/register a new `UiTextureResource` from validated texture data, then assign its typed reference to `ItemInfo.iconImage`.

Do not claim imported icon support until a live fixture proves all three stages: resource registration, `iconImage` assignment, and visible in-game rendering. A PNG import alone is insufficient because the runtime texture payload and reference representation are still build-specific.

## Vanilla reference pair recovered from the KFC exports

The exported `ItemInfo` data contains many non-null examples. One verified pair is:

- `iconImage`: `b7eb722c-ed5d-48d8-93c8-a68f6ef342d0`
- matching `keen::UiTextureResource` file: `b7eb722c-ed5d-48d8-93c8-a68f6ef342d0_f9e86997_0.json`
- resource `$guid`: `b7eb722c-ed5d-48d8-93c8-a68f6ef342d0`
- debug name: `buildings_roof_ShinglesDesert_01_icon`
- dimensions: 512 × 512
- format: `R8G8B8A8_unorm`
- mip levels: 1
- tiled: false

This proves that the `iconImage` value matches the texture resource `$guid` in the current export. The filename also carries an archive/resource identity suffix (`f9e86997`) and part number, so the implementation must preserve the GUID, archive identity, and part relationship when cloning or importing an icon.

## Next probe

Inspect a vanilla item whose `iconImage` is non-null, record the serialized reference value and the corresponding `UiTextureResource` GUID/data metadata, then create a donor-icon clone with a fresh resource GUID. Keep the current model/scene bed fixture as the rollback path.

