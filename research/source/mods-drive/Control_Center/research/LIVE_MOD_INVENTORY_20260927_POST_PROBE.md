# Live mod inventory after visual-model probe — 2026-09-27

The temporary generated probe `full_icon_model_bed_probe_20260927_v2` is not
present in the live mods directory after cleanup.

The live directory currently contains these pre-existing modules:

| Directory | Observed state |
|---|---|
| `combined_localized_bed_probe_1076226` | research-only |
| `content_donor_probe_1076226` | legacy manifest without feature state |
| `flight_mod` | legacy manifest without feature state |
| `registry_clone_probe_20260927_v24` | research-only |
| `registry_clone_probe_20260927_v26` | research-only |
| `registry_clone_probe_20260927_v27` | research-only |
| `registry_clone_probe_20260927_v29` | research-only |

This inventory is observational. No pre-existing module was removed or changed
during the probe cleanup. The old research probes should be reviewed or
quarantined before a future clean live smoke test if isolation is required.
