# ItemColorCombination recolor probe — 2026-09-29

## Scope

This isolated research probe tested the `keen::ItemInfo.itemColorCombinationSetup`
field on the known-good cloned bed path for build
`1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z`.

The reflected field is `keen::ItemColorCombination` (type index 3841):

- `color0`, `color1`, and `color2` use the `keen::Color` type;
- `isSet` is a hidden boolean;
- the registry default is three white RGBA colors with `isSet=false`.

## Probe input

The probe attempted three distinct RGBA colors and `isSet=true`:

```lua
clone.data.itemColorCombinationSetup = {
    color0 = { 180, 60, 60, 255 },
    color1 = { 45, 110, 210, 255 },
    color2 = { 220, 180, 45, 255 },
    isSet = true,
}
```

## Result

**Research-only / unresolved boundary — not a recolor success.**

The loader successfully started the isolated module and emitted the clone and
catalog-preview markers immediately before the assignment. It emitted no
`CATALOG_RENDER_CONTROL` marker afterward, and there was no catalog, item-info,
or placed-world screenshot proving a color change. The field therefore cannot
be promoted to the stable Content Studio workflow from this run.

This result does not prove that the engine cannot recolor items. It shows that
the current Lua table representation is not a verified assignment route on this
build. The next investigation must resolve the `keen::Color` binding or locate
the referenced color-combination resource graph before another runtime attempt.

## Safety and cleanup

- The probe was installed only in the isolated research profile.
- `TemplateResource` quarantine was explicitly approved for this boundary probe.
- The probe was removed after the run.
- Enshrouded was stopped after cleanup.
- The live mods directory contains only the stable `enshrouded_mod_hub` and
  `flight_mod` entries.

Evidence files:

- `research/R38_ITEM_COLORS_DRYRUN.json`
- `research/R38_ITEM_COLORS_INSTALL.json`
- `research/R38_ITEM_COLORS_SESSION.json`
- `research/R38_ITEM_COLORS_LAUNCH.json`
- `research/R38_ITEM_COLORS_REMOVE.json`
