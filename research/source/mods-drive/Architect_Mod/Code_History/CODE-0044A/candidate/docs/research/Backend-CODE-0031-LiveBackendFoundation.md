# CODE-0031 — Live Backend Capability and NativeMemoryAdapter Foundation

## Status

- Framework: `FRAMEWORK_IMPLEMENTED`
- Runtime read: `NO_SAFE_MEMORY_READ_TARGET_AVAILABLE`
- Runtime mutation: not proven

CODE-0031 hardens the CODE-0030 implementation. It does not resume GameSettings or cursor/ECS research and does not change the v0.38.0 native DLL.

## Architecture

`AdminAction` schema v2 selects exactly one mechanism from `LUA_API`, `VANILLA_ACTION`, `RESOURCE`, `NATIVE_OBJECT`, `NATIVE_MEMORY`, `NATIVE_HOOK`, or `NONE`. The independent domain adapter, evidence, runtime mode, authority, persistence, risk, readback, revert, failure, and enabled fields remain intact.

The centralized BackendRouter dispatches only to the declared backend. Invalid and unavailable backends fail explicitly. There is no fallback to native memory or hooks.

Disabled action families now record intended research mechanisms without claiming support:

- Player vital families: `NATIVE_MEMORY`
- Movement and item-object families: `NATIVE_OBJECT`
- Crafting/world/camera/glider/building families: `RESOURCE`
- Multiplayer families: `VANILLA_ACTION`
- GameSettings: `NONE`, with candidate mechanisms recorded separately

## NativeObjectAdapter

NativeObjectAdapter is separate from scalar memory access. It registers a named object resolver and an allowlist of named operations only after exact-build evidence is supplied. Unknown objects return `OBJECT_UNRESOLVED`; unregistered operations return `ACTION_UNSUPPORTED`. No raw pointer or address is accepted from F7 or Lua. No Player, Camera, Inventory, or GameSettings object is registered in CODE-0031.

## NativeMemoryAdapter

The PowerShell boundary stores only named target metadata and delegates guarded resolution/access to native code. It never receives an address. The native contract defines bounded scalar types, exact-build target descriptors, master-gate requirements, readback failure, and revert state. There are zero registered targets because no existing path proves a live owner, field layout, and independent runtime readback simultaneously.

The mutation gate requires build support, sufficient target evidence, resolution, pointer/page and value sanity, readback, action enablement, and the global gate. Future writes must capture the original value, perform one scoped write, immediately read back, return `FAILED_READBACK` on disagreement, and retain `ORIGINAL_SESSION_VALUE` when revert is supported. `KNOWN_VANILLA_DEFAULT` remains independent evidence.

## Lua / EML and scripting

The capability matrix remains in `bridge/backend_capabilities.json`. Proven facilities are `require`, `print`, restricted `io.export`, and restricted `game.assets` resource APIs. LuaJIT, FFI, `package.loadlib`, DLL calls, general filesystem/environment access, and callbacks remain unresolved.

The existing command bridge is the supported Lua-to-Architect design. Future scripts may call a named `Architect.Command(...)` facade only after a command is registered and enabled. No scripting API exposes offsets, signatures, pointers, or memory primitives.

## F7 diagnostics and runtime validation

`backend.capabilities` reports adapter status, build support, mutation gate, target counts, last action, and last failure. Expected CODE-0031 values are zero registered/readable/writable memory targets and mutation gate false.

For an in-game UI check, invoke `backend.capabilities` and return:

- `bridge/backend_capabilities.json`
- `bridge/admin_state.json`
- `bridge/executor_ack.json`
- `bridge/executor.log`
- `bridge/native_status.json`

## First reversible mutation recommendation and blocker

No mutation is ready. The best research candidate remains a session-local resource scalar such as camera FOV because persistence risk and revert complexity should be low. The exact blocker is absence of a proven live resource owner/consumer, refresh mechanism, and authoritative readback. The required next experiment is read-only: identify the live resource instance and demonstrate that two independent observations agree before any write is designed.
