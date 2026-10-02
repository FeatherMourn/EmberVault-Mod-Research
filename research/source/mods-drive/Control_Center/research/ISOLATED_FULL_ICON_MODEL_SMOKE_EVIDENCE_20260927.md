# Isolated Full Icon/Model Bed Smoke Evidence — 2026-09-27

## Purpose

Validate the runtime registration path for the generated full-icon/model bed probe while all other live modules are quarantined. This isolates loader behavior from interactions among the existing research modules.

## Profile and isolation

- Profile: `research/isolated_smoke_profile_20260927.json`
- Profile ID: `isolated_content_smoke_1076226`
- Excluded modules: all seven modules that were live before the run
- Temporary probe: `full_icon_model_bed_probe_20260927_v2`
- Probe item ID: `3987654507`
- Probe recipe ID: `3987654508`

The Control Center quarantine workflow moved the seven existing module directories to reversible quarantine records before launch. After the run, all seven records were restored successfully. The temporary probe directory was removed before restoration.

## Runtime result

The EML log contained these expected markers:

```text
DONOR_SCAN_DONE|true
CLONED_ITEM|3987654507
REGISTERED_RECIPE|3987654508
```

No panic, fatal, or error markers were found in the searched run output. The generated probe therefore confirms:

- donor discovery completed;
- a new item resource was registered;
- a new recipe resource was registered;
- the isolated loader path remained stable during the run.

## Cleanup verification

Post-run live verification reported:

- loader status: `ready`;
- live module count: 7;
- research-only module count: 5;
- temporary probe present: `false`;
- newest live EML log: approximately 1.3 MB.

The normal live inventory was restored. The remaining warning about research-only modules is expected until a production profile is selected.

## What this does not prove

This run did not visually inspect the Carpenter catalog, item icon, placed model, materials, or texture appearance. It proves runtime registration and stability only; visual substitution remains research-only until a controlled in-game inspection confirms it.

The staged artifact used for this run was compiled before donor-candidate log reduction, so its historical log was noisier than future builds should be. The source-side generator has since been updated to suppress repetitive donor-candidate markers.

## Recovery record

Quarantine records were written under:

`profiles/quarantine-records/`

The workflow is reversible through `tools/apply_smoke_profile.py --restore` using the same profile.
