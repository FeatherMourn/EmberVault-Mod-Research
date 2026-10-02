# Render-model GUID evidence — 2026-09-27

## Runtime result

- Probe: `single_render_model_probe_20260927`
- Resource type: `keen::RenderModel`
- GUID: `4c7f1c3a-b448-4460-ad5e-a79b3859d2c1`
- Result: `true`
- Resource count: `12713`
- Session log: `H:\SteamLibrary\steamapps\common\Enshrouded\logs\2026-09-27.eml.log`
- Backup: `H:\Enshrouded_ControlCenter_Backups\20260927-single-render-model-probe`

## Interpretation

The bed's discovered model GUID is confirmed as a runtime `keen::RenderModel`
resource on this EML/game build. This is stronger evidence than the previous
multi-family probe and establishes a concrete target for future donor-preserving
model substitution experiments.

This does not yet prove that assigning a different `RenderModel` to a cloned
furniture item changes its placed appearance. The template/object graph and
mechanics-preservation behavior still require separate testing.

## Capability status

`experimental`: GUID-to-resource-family resolution is runtime-verified;
visual substitution remains research-only.
