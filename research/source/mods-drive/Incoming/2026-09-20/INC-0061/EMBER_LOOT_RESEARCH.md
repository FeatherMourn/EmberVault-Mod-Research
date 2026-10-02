# Ember loot research — 2026-09-20

Status: EXTERNAL ARTIFACT OBSERVED. These findings describe the uploaded Ember artifact, not proven Architect behavior on Enshrouded build 1076226.

## Source files inspected
- `Ember/src/Config/Loot_Tweaks_Config.lua`
- `Ember/src/Features/Loot_Tweaks.lua`
- `Ember/src/Features/ExpandedGameSettings.lua`
- `Ember/src/Config/ExpandedGameSettings_Config.lua`

## Observed configuration
Ember exposes `Enable_LootTweaks` plus separate numeric controls for `Loot_ResourceDropMultiplier`, `Loot_ItemDropMultiplier`, and `Loot_MaxStackSize`.
Its own comments classify `Loot_ItemDropMultiplier` as affecting "Dropped Loot" including chests, enemies, destructibles, etc.
It also defines safety clamps for drop multipliers and maximum loot-table stack size.

## Observed quantity mechanisms
`Loot_Tweaks.lua` enumerates `keen::ItemInfo` resources. For stackable items with `randomLootStackRange`, it scales both `minStackSize` and `maxStackSize` by the item loot multiplier.
The same feature enumerates `keen::LootableItemsResource` resources and, for stackable entries, scales `stackSizeMin` and `stackSizeMax`; it can also set `stackSizeMaxScaled` and disable `stackSizeScalable` for the modified entry.
It also scales `countMin` and `countMax` in relevant `keen::ecs::DefaultInventoryResource` stacks.
These observations are direct evidence that the artifact can alter quantity ranges used by loot/resource data, including chest-classified dropped loot according to its own configuration comments.

## Expanded game setting
Ember's expanded game settings maps a user-facing `dropAmount` setting to `resourceDropStackAmountFactor`. This is a separate setting path from its direct loot-resource edits.

## What the inspected source does NOT establish
The inspected Ember loot feature does not expose an explicit chest-quality selector, silver-vs-gold chest editor, rarity-weight control, or "upgrade chest loot rarity" field.
No explicit loot-entry probability/weight field is modified by this feature.
Therefore, changing the *amount* of loot is supported by the external artifact evidence, while changing the *quality/rarity distribution* of silver/golden chest rewards remains UNSOLVED for Architect until the current game's chest/loot ownership and selection fields are mapped.

## Architect research hypothesis
A safe next step is observe-only enumeration of current-build `keen::LootableItemsResource` and the chest/template resources that reference it. Capture the resource identity for silver and golden chests, their loot entries, all available fields, and the generated result across repeated opens on a test world. Then determine whether rarity/quality is controlled by the chest resource, the loot table, item rarity filtering, a weighted selection field, or a higher-level chest tier mechanism. Do not invent field names or mutate until that mapping is proven.
