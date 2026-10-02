# CODE-0030 — Live Backend Capability Probe and NativeMemoryAdapter Foundation

## Outcome

- Backend framework: `FRAMEWORK_IMPLEMENTED`
- Runtime native-memory read: `NO_SAFE_MEMORY_READ_TARGET_AVAILABLE`
- Runtime native-memory mutation: `NOT_PROVEN`

No guessed target was registered. The native runtime DLL remains v0.38.0 and unchanged. The Entity Inspector, PlayerObserver, and GameSettings conclusions remain fail closed.

## Lua / EML capabilities

| Capability | Status | Local evidence |
|---|---|---|
| Lua version/runtime identity | UNRESOLVED | No captured runtime/version API |
| `require` | AVAILABLE | Protected load of `Config.Architect_Blueprint_Config` |
| `package`, `package.loadlib` | UNRESOLVED | No supported use; `require` alone is insufficient |
| LuaJIT / `ffi` | UNRESOLVED | No runtime identity or FFI evidence |
| `debug` | UNRESOLVED | No use/capture |
| `io` / filesystem | AVAILABLE_RESTRICTED | Host `io.export` only |
| `os` / environment variables | UNRESOLVED | No evidence |
| Native modules / DLL exports | UNRESOLVED | No host binding demonstrated |
| Host bindings | AVAILABLE_RESTRICTED | `game.assets` get/create APIs |
| EML resource APIs | AVAILABLE_RESTRICTED | Resource enumeration, lookup, creation |
| Callbacks/events | UNRESOLVED | No registration surface present |
| Console/log | AVAILABLE | `print` |
| Reload | AVAILABLE_RESTRICTED | Existing configuration requires startup/full restart |

Absence of source usage is reported as unresolved rather than proof that a library cannot exist. Dangerous facilities were not activated to test availability.

## Lua-to-Architect decision

Use the existing named command bridge. No supported direct Lua-to-DLL/export facility is proven. Lua must never receive game addresses or raw memory operations. A future scripting facade may expose `Architect.Command(commandId, value)`, but only for commands already registered and enabled by the central catalog.

## Backend schema and router

AdminAction schema v2 adds `backend`, restricted to:

`LUA_API`, `VANILLA_ACTION`, `RESOURCE`, `NATIVE_OBJECT`, `NATIVE_MEMORY`, `NATIVE_HOOK`, `NONE`.

`backendAdapter` remains the domain adapter identity. Backend selection does not change evidence or enabled state. GameSettings rows preserve candidates `RESOURCE`, `VANILLA_ACTION`, `NATIVE_OBJECT`, and `NATIVE_MEMORY` without selecting or enabling one.

`BackendRouter.psm1` performs exact routing. Missing handlers return `BACKEND_UNAVAILABLE`; invalid kinds return `INVALID_BACKEND`; unsupported-build native-memory requests return `BUILD_UNSUPPORTED`. There is no implicit fallback.

## NativeMemoryAdapter contract

The native header defines registered named targets, scalar value types, status codes, mutation state, and the master gate. No API accepts a user-controlled address. CODE-0030 registers zero targets.

Future target resolution must validate exact build, compiled resolver, evidence, page permissions, pointer/alignment, type/range, and target-specific sanity. Mutation additionally requires action enablement, the centralized master gate, writable target declaration, and readback availability.

Mutation sequence:

1. Resolve registered target.
2. Read and validate original.
3. Validate requested value.
4. Perform one scoped write.
5. Read back immediately.
6. Return `FAILED_READBACK` on mismatch.
7. Retain the original session value when revert is supported.

`ORIGINAL_SESSION_VALUE` is distinct from `KNOWN_VANILLA_DEFAULT`; the latter requires independent evidence.

## Diagnostics

F7 Inspector / Diagnostics contains `backend.capabilities`, backed by `bridge/backend_capabilities.json`. It reports Lua status, adapter availability, build support, mutation gate, registered/readable/writable target counts, last action, and last failure without raw addresses.

## Runtime test

No game launch is required to validate this partial-success result. Start Architect normally and invoke `backend.capabilities`; expected values are zero registered/readable/writable memory targets, mutation gate false, and `NO_SAFE_MEMORY_READ_TARGET_AVAILABLE`.

Return `bridge/backend_capabilities.json`, `bridge/admin_state.json`, `bridge/executor_ack.json`, `bridge/executor.log`, and `bridge/native_status.json` if validating the F7 display in game.

## First reversible mutation recommendation

No mutation is presently recommended for implementation. The first candidate should be a session-local `RESOURCE` scalar with a proven live refresh path and independent readback, because it ranks above native memory and can retain an original session value. Camera FOV is a reasonable research target, but it remains disabled until its live resource consumer and refresh/readback behavior are proven.
