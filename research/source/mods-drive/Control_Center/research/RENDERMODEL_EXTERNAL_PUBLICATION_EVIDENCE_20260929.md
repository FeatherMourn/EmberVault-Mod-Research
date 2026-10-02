# RenderModel external publication evidence — build 1076226

The registered visual substitution probe was run through the validated external
EML patch route on a disposable game copy.

## Result

- The cloned `ItemInfo` accepted a replacement `iconModel` GUID.
- Item, item-registry, recipe, knowledge, UI-link, and recipe-GUID checks all passed.
- Archive registration completed successfully.
- The probe was removed transactionally afterward.
- The live installation was not modified.

Evidence: `research/probe_sessions/external_route_render_model_variant_20260929.json`.

A direct-client startup smoke test on the same disposable copy kept
`enshrouded.exe` alive for 15 seconds without a crash, then terminated it for
cleanup. Evidence: `research/probe_sessions/external_route_render_model_startup_smoke_20260929.json`.

## Boundary

`client_rendering_verified` remains false. The result proves that the
RenderModel substitution survives the external publication route; it does not
yet prove that the Carpenter catalog displays the replacement appearance or
that a placed object renders it. Those require controlled in-game screenshots
and remain research-only.
