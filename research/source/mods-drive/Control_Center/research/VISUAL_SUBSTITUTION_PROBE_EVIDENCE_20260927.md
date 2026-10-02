# Visual substitution probe evidence — 2026-09-27

## Probe

- Project: `visual_substitution_probe_20260927`
- Resource family: `keen::RenderModel`
- Session log: `H:\SteamLibrary\steamapps\common\Enshrouded\logs\2026-09-27.eml.log`
- Backup: `H:\Enshrouded_ControlCenter_Backups\20260927-visual-substitution-probe-smoke`

## Fresh-session result

EML executed the read-only probe successfully. The log reported:

```text
DEPENDENCY|research-model-guid|false
DEPENDENCY|research-material-guid|false
GRAPH_SCAN|keen::RenderModel|count=12713
ACTION|read_only_no_visual_mutation
```

## Interpretation

- The EML Lua route can enumerate the target render-model resource family at
  runtime.
- The probe correctly distinguishes unavailable dependency GUIDs from the
  resource-family count.
- No visual mutation was attempted, so this does not prove arbitrary model
  substitution or custom asset import.
- The active live probe directory was removed after the smoke test; the stable
  live mods were preserved.

## Capability status

`experimental`: runtime resource-family discovery is verified for this session;
visual replacement remains research-only until a donor-specific resource graph
and in-game visual/rollback evidence are obtained.
