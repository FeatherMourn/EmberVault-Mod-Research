# CODE-0032 — Camera FOV Live Resource Discovery

## Conclusion

Primary: `FOV_STATIC_CANDIDATES_ONLY`

Mutation readiness: `MUTATION_BLOCKED`

The current-build reflection data establishes configuration, camera-mode, runtime-state, scene, UI, and derived-render FOV-shaped fields. It does not establish a loaded resource instance, active gameplay owner, propagation/refresh consumer, or independent effective-FOV readback. No read-only target was registered and the native runtime remains unchanged.

## Static candidates

| Type/index | Field | Offset | Default | Classification | Finding |
|---|---|---:|---:|---|---|
| `GraphicsSettings` 7028 | `fov` | `+0x00` | 65.0 | STATIC_CONFIG | Strong user-option input candidate; live settings owner and propagation unresolved |
| `FOVModifierSettings` 1972 | `fov` | `+0x00` | 50.0 | CAMERA_MODE_PROFILE | Range attributes 0–180; nested profile, not active camera proof |
| `CameraModifierConfig` 1990 | `fovSettings` | `+0x2C0` | 50.0 | CAMERA_MODE_PROFILE | Full modifier aggregate |
| `CameraSimpleConfig` 1992 | `fovSettings` | `+0xB8` | 50.0 | CAMERA_MODE_PROFILE | Simple mode profile |
| `CameraStatesManager` 1994 | `cameraStates` | `+0x00` | — | CAMERA_MODE_PROFILE | 45 `CameraStateConfig` records |
| `ClientCamera` 2759 | `fovY` | `+0x2C` | 0.0 | RUNTIME_STATE | Best effective-value candidate; embedded in `ClientPlayerInputData` at `+0x20` |
| `DebugMessageCamera` 1609 | `fov` | `+0x748` | 0.0 | RUNTIME_STATE | Potential diagnostic readback, but producer/access unresolved |
| `SceneCamera` 3920 | `fovY` | `+0x60` | ~0.52 | CAMERA_MODE_PROFILE | Scene/cinematic candidate, not normal gameplay |
| `FbUiCharacterView` 4379 | `fov` | `+0x18` | — | UI_ONLY | Rejected as gameplay owner |
| `Fsr3UpscalerConstants` 5268 | `fTanHalfFOV` | `+0x6C` | — | UNKNOWN | Derived render constant, not an owner |

All offsets and defaults above are reflection facts for build 1076226. Defaults do not establish current runtime values.

## Resource and loading evidence

`Game38RootObjects.playerCameraStatesManager +0x460` and `Game38SharedResources.playerCameraStatesManager +0x270` prove that the camera-state manager is resource-shaped and referenced by root/shared resource schemas. The local Architect data index reports zero `camera_states` rows and `UNAVAILABLE` coverage, so it cannot supply a GUID, hash, path, or loaded instance.

The restricted Lua environment can identify/enumerate a known resource type through `game.assets` in principle. No local capture proves that `CameraStatesManager` is exposed through that API, which instance is loaded, or whether edits would refresh. CODE-0032 performs no resource mutation.

## Owner, consumer, and readback

The strongest unproven chain is:

```text
GraphicsSettings.fov
    → CameraStatesManager / active CameraStateConfig FOV
    → ClientPlayerInputData.camera.ClientCamera.fovY
```

Each node has static type evidence; no data-flow evidence currently connects them.

- Live owner: `UNRESOLVED`
- Consumer/refresh: `UNKNOWN`
- Refresh classification: `UNKNOWN`, not LIVE or SESSION
- Independent readback: `UNRESOLVED`
- Best readback candidate: `ClientCamera.fovY +0x2C`
- Diagnostic alternative: `DebugMessageCamera.fov +0x748`

Neither runtime candidate has a validated live component/message instance or resolver. Reading it would require guessed ownership, so NativeObject and NativeMemory registration are rejected.

## Camera modes

The 45-entry `CameraStatesManager` and explicit `CameraId` fields prove a multi-mode model. Normal, aiming/zoom, building, gliding, and cinematic FOVs must not be collapsed. `SceneCamera` is kept separate. No current evidence maps a numeric CameraId to the requested normal gameplay mode.

## Backend and F7

Preferred future backend remains `RESOURCE`, with `NATIVE_OBJECT` as a possible alternative if a live camera object is proven. Current backend is `NONE`. NativeMemory is not eligible.

The existing disabled `camera.fov` family remains `RESOURCE`-classified but unproven and disabled. No slider, setter, mutation command, or current-value display was enabled. `bridge/camera_fov_state.json` supplies bounded diagnostics without guessed values.

## Runtime experiment

No safe runtime observation path exists yet, so an in-game multi-mode capture would not produce trustworthy FOV values. The next read-only experiment is to determine whether restricted `game.assets.get_resources_by_type` exposes `keen::CameraStatesManager`, recording only resource identity and profile data. If that succeeds, compare normal, aim, build, gliding, and return-to-normal contexts without changing fields.

Return, if such a future capture is implemented:

- `bridge/camera_fov_state.json`
- the bounded camera resource inventory
- `bridge/backend_capabilities.json`
- `bridge/native_status.json`
- `bridge/native_runtime.log`

## Exact blocker before a write

Architect still lacks all three required runtime facts: the loaded authoritative owner, the consumer/refresh boundary, and an independent effective-value readback. Until they converge, even a resource write cannot pass the mutation gate.
