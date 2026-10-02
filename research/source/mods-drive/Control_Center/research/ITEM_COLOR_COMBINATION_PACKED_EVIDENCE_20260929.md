# Packed item-color assignment evidence — 2026-09-29

## Result

The second isolated recolor probe succeeded at the EML assignment boundary on
game build `1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z`.

`keen::Color` is a packed unsigned 32-bit value, not an RGBA Lua array. The
probe assigned:

```lua
clone.data.itemColorCombinationSetup = {
    color0 = 0xFF3C3CB4,
    color1 = 0xFFD26E2D,
    color2 = 0xFF2DB4DC,
    isSet = true,
}
```

The fresh EML log recorded:

```text
CATALOG_RENDER_CONTROL|field=itemColorCombinationPacked|ok=true|error=|value={"isSet":true,"color0":4282137780,"color1":4291980845,"color2":4281185500}
```

The clone was indexed afterward and the session completed without a panic. This
proves that Control Center/EML can write the typed packed color combination on
the cloned `ItemInfo` resource.

## Promotion status

**Research-only / visual proof still required.** This run did not capture a
catalog tile, item-information panel, or placed-world screenshot, so it does
not yet prove that the renderer consumes the values or that the saved object
visibly changes color. Content Studio must not present this as a stable
recolor feature until those runtime views are verified.

## Cleanup

- The probe used the isolated research profile and explicit quarantine override.
- It was removed immediately after the run.
- Enshrouded was stopped.
- The live mods directory contains only `enshrouded_mod_hub` and `flight_mod`.

Evidence files:

- `research/R39_ITEM_COLORS_INSTALL.json`
- `research/R39_ITEM_COLORS_SESSION.json`
- `research/R39_ITEM_COLORS_LAUNCH.json`
- `research/R39_ITEM_COLORS_REMOVE.json`
