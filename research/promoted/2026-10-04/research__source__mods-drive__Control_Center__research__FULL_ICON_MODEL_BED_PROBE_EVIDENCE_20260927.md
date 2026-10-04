# Full icon-model bed probe evidence — 2026-09-27

## Runtime probe

- Probe: `full_icon_model_bed_probe_20260927`
- Donor item ID: `2940001508`
- Intended clone item ID: `3987654503`
- Intended clone recipe ID: `3987654504`
- Donor recipe ID: `3531872774`
- Replacement `RenderModel`: `1ac410c2-c85e-4172-95eb-19b5b593118d`
- Backup: `H:\Enshrouded_ControlCenter_Backups\20260927-full-icon-model-bed-probe`

## Result

The runtime loaded the probe and registered the cloned `ItemInfo`:

```text
DONOR_SCAN_DONE|true
CLONED_ITEM|3987654503
BLOCKED|donor_recipe_not_found
```

The downstream content probe also observed the new item ID, with the cloned
bed's placed entity still present. No new recipe or UI entry was registered in
this run because the recipe lookup was blocked before the recipe/UI phase.

## Interpretation

This run confirms that the full-route probe can reach item cloning and retain
the requested replacement `iconModel` assignment path, but it does not prove
that the replacement model is displayed in the inventory icon or used by the
placed furniture. It also does not prove the complete recipe/UI route because
the donor recipe was not found during this run.

The likely next investigation is load-order/readiness: compare the successful
stable bed probe's recipe lookup timing and registry access with this generated
probe. The visual assignment result remains experimental until a clone with a
working recipe/UI entry is inspected in-game and rolled back successfully.

## Cleanup

- Enshrouded process stopped after evidence capture.
- Temporary live probe folder removed.
- Backup retained for rollback and comparison.

## Capability status

`experimental`: item-level visual-reference assignment is runtime-verified;
full recipe/UI integration for this generated probe was inconclusive; visible
model substitution remains unproven.
