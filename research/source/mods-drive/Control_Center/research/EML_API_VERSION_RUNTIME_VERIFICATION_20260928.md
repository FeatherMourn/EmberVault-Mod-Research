# EML Lua API version runtime verification — 2026-09-28

## Result

The rebuilt EML proxy emitted its declared Lua API contract version during a
fresh Enshrouded startup. Control Center read the current-session event as
API `1.3` and identified the current game build as `1076226`.

The session reached `Running mods...`, executed the stable hub, applied 1,910
patches, and attached the runtime loader without a current-session EML error.
The preceding isolated session used metadata-only GUID lookup to resolve all
32 animation dependencies, after which the probe was removed and the stable
profile restored.

## Evidence

- Fresh-session launch records:
  - `research/EML_API_VERSION_RUNTIME_SESSION_20260928.json`
  - `research/EML_API_VERSION_FULL_STARTUP_20260928.json`
- Machine-readable evidence: `research/EML_API_VERSION_RUNTIME_EVIDENCE_20260928.json`
- Evidence validator: `tools/verify_loader_api_runtime.py`; the validator is
  included in the milestone gate and has regression tests for stale sessions
  and current-session loader errors.
- EML log: `H:\SteamLibrary\steamapps\common\Enshrouded\logs\2026-09-28.eml.log`
- Current API event: `2026-09-28T21:22:16Z`, `api_version: 1.3`.
- The event followed a type-registry record for
  `1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z`.
- The Control Center runtime evidence reports build `1076226`, API `1.3`,
  observed mod execution, and zero current-session errors.
- No panic, fatal, or error-level event occurred in the fresh session.
- Enshrouded is closed.

## Build and recovery

- Release build command: `cargo build --release -p mod-loader-lua -p dinput8-proxy`.
- Installed proxy SHA-256:
  `61DEB4A625E919A1BCA56C751E7AC01E3821B982C9FE464B2CD091F2BD6766A2`.
- The installed DLL hash matched the rebuilt source artifact.
- Previous installed proxy is backed up at
  `H:\Enshrouded_LiveBackup_20260928_api_1_3\dinput8_api_1_2.dll`
  with SHA-256
  `B01FBE47A76283B1A715EC98A9DF219D6CDFE10E15E6A85E7387FE61C0EDA1EE`.
- The game was closed before replacement. The replacement is reversible by
  copying the recorded backup DLL back to the game directory.

## Scope and remaining validation

Control Center now extracts API versions only from after the newest EML type
registry event, avoiding stale API values from earlier launches. Runtime health
also derives its game build from that same latest registry event rather than
from unrelated numeric log content. Compatibility evaluation and health-report
output consume the detected API version; missing runtime evidence remains
unknown instead of defaulting to a hard-coded version.

This does not establish compatibility with other EML releases or game builds.
Those still require build-specific runtime evidence and updated compatibility
records.
