# Item visual-reference assignment live boundary

Date: 2026-09-27  
Target build: `1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z`

## Probe

- Probe: `item_visual_reference_159b_live_20260927`
- Donor `ItemInfo` GUID: `01474f79-6b5a-4bcd-999d-7e9339fda91c`
- Clone item ID: `3987654491`
- Replacement `RenderModel` GUID: `159b5f47-aa61-4db9-8e64-06db850de6f6`
- Mode: clone-only, no registry mutation

## Observed result

The fresh EML session recorded:

```text
ASSIGN|true|
BEFORE|4c7f1c3a-b448-4460-ad5e-a79b3859d2c1
AFTER|159b5f47-aa61-4db9-8e64-06db850de6f6
ACTION|clone_only_no_registry_mutation
```

The assignment was accepted on the independent clone. The game remained
running and no panic was observed. The probe was stopped and removed after the
session; the stable live module inventory was restored.

## Boundary

This verifies that an `ItemInfo` clone accepts a different `RenderModel` GUID.
It does **not** verify that the placed furniture object uses that model in-game.
The next gate is a controlled registry/UI clone with a visible placed-object
check, followed by donor-preservation and rollback evidence. Until then,
visual substitution remains experimental/research-only.
