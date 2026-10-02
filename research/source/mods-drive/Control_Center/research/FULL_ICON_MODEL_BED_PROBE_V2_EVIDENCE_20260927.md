# Full icon-model bed probe v2 — 2026-09-27

## Runtime evidence

- Probe: `full_icon_model_bed_probe_20260927_v2`
- Donor item: `2940001508`
- Clone item: `3987654507`
- Donor recipe: `3531872774`
- Clone recipe: `3987654508`
- Requested replacement `RenderModel`: `1ac410c2-c85e-4172-95eb-19b5b593118d`
- Backup: `H:\Enshrouded_ControlCenter_Backups\20260927-full-icon-model-bed-probe-v2`

The generated module produced these markers in the live EML log:

```text
DONOR_SCAN_DONE|true
CLONED_ITEM|3987654507
REGISTERED_RECIPE|3987654508
```

No panic, fatal error, or mod-loading error was observed for this probe.

## Interpretation

The generator fix is validated: the complete generated item-to-recipe route
now reaches recipe registration. The earlier failure was caused by comparing a
recipe output item to the donor recipe ID. The corrected lookup matches the
recipe ID or the donor item output and supports both known registry types.

This run still does not prove that the replacement model is visibly rendered.
The generated route does not yet emit a verified UI-registration marker, and no
in-game visual inspection was performed in this smoke run. The capability
remains experimental until the clone is confirmed in the Carpenter UI and its
placed appearance is compared with the donor.

## Cleanup

- Enshrouded was stopped after log capture.
- Temporary live probe folder was removed.
- The rollback backup was retained.

## Capability status

`experimental`: generated item and recipe registration are live-verified;
visual-model substitution and UI visibility remain unverified.
