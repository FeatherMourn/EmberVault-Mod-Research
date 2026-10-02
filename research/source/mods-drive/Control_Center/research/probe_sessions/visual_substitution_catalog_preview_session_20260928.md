# Visual-substitution catalog-preview session — 2026-09-28

## Scope

This was an isolated run of `registered_visual_substitution_probe_20260928`
against game/EML build:

`1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z`

The stable profile was restored after the run. The probe was not left
installed.

## Runtime evidence

- Fresh EML session observed after baseline log size `248105` bytes.
- Probe was accepted and executed without a panic.
- Clone registration completed: item `3987654501`, recipe `3987654502`.
- Registry counts changed independently: items `3520 -> 3521`, recipes
  `1954 -> 1955`.
- UI set cloning completed: `sets=8 -> 9`, new entry value `3987654502`.
- The catalog-preview fields did not change in this run:
  - `iconImage`: zero GUID before and after.
  - `iconModel`: donor model GUID before and after.
  - `iconScene`: donor scene GUID before and after.
- The visual-assignment marker reported `ok=true`, but the observed model
  reference remained the donor GUID in this session.

## Verdict

`partial / research-only`

This session confirms safe clone, recipe, and UI registration but does not
prove catalog visual substitution. It does not promote icon, model, scene,
material, texture, or color substitution. A future candidate must change one
preview field at a time and provide matching catalog and placed-object
screenshots before promotion.

## Recovery evidence

- Game stopped before cleanup.
- Probe transaction restored using backup
  `20260928-023353-1790588033867454300`.
- Empty probe directory removed.
- Final live-loader preflight: compatible build, stable module only, zero
  research modules, zero unclassified modules, `isolation_ready=true`.

## Source log

`H:\SteamLibrary\steamapps\common\Enshrouded\logs\2026-09-28.eml.log`

