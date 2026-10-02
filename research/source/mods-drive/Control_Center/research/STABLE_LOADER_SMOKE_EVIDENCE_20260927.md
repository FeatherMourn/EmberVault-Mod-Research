# Stable loader smoke evidence — 2026-09-27

## Scope

Validate the production profile after log rotation and generated-manifest
repair, without enabling research-only modules or changing the DLL.

## Result

**Verified — fresh stable session.**

- Enshrouded was launched while no game process was already running.
- A new log was created at `H:\SteamLibrary\steamapps\common\Enshrouded\logs\2026-09-27.eml.log`.
- EML loaded build `1076226` and ran the stable `enshrouded_mod_hub`.
- The five verified tuning modules completed their markers:
  loot/drop rates, music/instruments, progression, survival QoL, and
  terraforming/mining.
- EML reported `Applied 1910 patches` and `Attaching runtime loader`.
- No panic, fatal, or error marker appeared in the observed fresh session.
- The process remained responsive after the observation window.

## Safety boundary

World/difficulty settings, content probes, visual substitution probes, and
localization probes were not enabled. This evidence validates launch and the
stable tuning profile only; it does not promote any research-only capability.
