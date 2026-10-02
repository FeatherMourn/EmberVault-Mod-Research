# Settings metadata probe evidence — 2026-09-27

## Result

The rebuilt EML proxy successfully ran the isolated read-only probe.

```text
CALL|keen::GameSettingsPresetsResource|true
COUNT|keen::GameSettingsPresetsResource|1
RESOURCE|keen::GameSettingsPresetsResource|46e14df6-fb8f-4f66-9463-e23b9e19e48e|0
CALL|keen::FbUiBundle|true
COUNT|keen::FbUiBundle|1
RESOURCE|keen::FbUiBundle|46e14df6-fb8f-4f66-9463-e23b9e19e48e|0
ACTION|metadata_only_no_decode_no_write
```

No native panic occurred during the probe. The game process was stopped after
the test and the original DLL and mods were restored from backup.

## Classification

Metadata discovery is now runtime-verified for both families on build
`1076226`. Payload decoding and writes remain research-only; this evidence does
not promote `world_and_difficulty` to verified status.

A follow-up read-only payload probe also successfully materialized the direct
`GameSettingsPresetsResource` by GUID and accessed its `data` field. A subsequent
full module write-path attempt did not produce a completion marker, so the
module remains disabled and the live installation was restored from backup.

The narrower single-field probe then confirmed that direct lookup, field read,
and a same-value write all succeed in isolation. When the same direct lookup
was reached after the other tuning modules in the generated hub, initialization
stalled at the world-settings entry point. The remaining issue is therefore an
inter-module/runtime interaction; the module stays disabled pending isolated
world-only and ordered-composition tests.
