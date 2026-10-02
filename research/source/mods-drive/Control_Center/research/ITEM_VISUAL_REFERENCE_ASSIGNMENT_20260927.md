# Item visual-reference assignment evidence — 2026-09-27

## Runtime probe

- Probe: `item_visual_reference_probe_20260927`
- Donor ItemInfo GUID: `01474f79-6b5a-4bcd-999d-7e9339fda91c`
- Clone item ID: `3987654501`
- Donor `iconModel`: `4c7f1c3a-b448-4460-ad5e-a79b3859d2c1`
- Replacement `RenderModel`: `1ac410c2-c85e-4172-95eb-19b5b593118d`
- Backup: `H:\Enshrouded_ControlCenter_Backups\20260927-item-visual-reference-probe`

## Result

```text
ASSIGN|true|
BEFORE|4c7f1c3a-b448-4460-ad5e-a79b3859d2c1
AFTER|1ac410c2-c85e-4172-95eb-19b5b593118d
ACTION|clone_only_no_registry_mutation
```

## Interpretation

EML accepts assignment of a different runtime `RenderModel` GUID to a cloned
ItemInfo `iconModel` field. This proves typed field assignment on the clone,
not that the game displays the replacement or that placed furniture appearance
has changed. The donor and registries were not modified.

## Capability status

`experimental`: clone-only visual-reference assignment is runtime-verified;
visible appearance substitution and placed-template replacement remain
research-only.
