# ItemInfo color runtime boundary — build 1076226

## Result

On 2026-09-29, a disposable-copy EML patch run added the following research-only
assignment to the independent bed clone:

```lua
clone.data.color = { r = 1.0, g = 0.12, b = 0.12, a = 1.0 }
```

The EML process terminated with the known Rust error `panic in a function that
cannot unwind` immediately after the probe started. No archive publication or
visual claim was made, and the reusable bed probe was restored to its prior
stable form.

## Interpretation

The current build does not safely accept this direct `ItemInfo.color` mutation
through the external EML route. This is stronger evidence than a missing
rendering screenshot: the field assignment itself is presently unsafe. It does
not rule out color changes through a RenderModel/material resource, a supported
variant structure, or an asset-package route.

## Evidence

- Failed disposable-copy run: `research/probe_sessions/external_route_color_variant_20260929.json`
- Stable external route revalidation: `research/probe_sessions/external_route_validation_followup_20260929.json`
- Reusable probe restored: `research/probes/bed_clone_injection_1076226/src/mod.lua`

The capability remains `research-only`.
