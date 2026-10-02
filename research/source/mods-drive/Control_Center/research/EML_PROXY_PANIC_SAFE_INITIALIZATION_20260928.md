# EML Proxy Panic-Safe Initialization

## Change

The local `dinput8-proxy` fork no longer unwinds through `DllMain` when EML initialization fails. Initialization errors from the mod environment, Lua runner, game-file discovery, and runtime-loader attachment are returned as recoverable errors and logged as:

`EML initialization skipped; game will run without EML mods`

The proxy continues to forward the system DirectInput exports, allowing the game to launch without the mod layer when a module or loader configuration is invalid.

File-log initialization is also recoverable: if the configured log directory cannot be opened, EML reports the failure on stdout and continues with stdout logging instead of panicking.

## Verification

- `cargo check -p dinput8-proxy` passed.
- Release `dinput8-proxy` build passed.
- Live deployment hash matches the release artifact.
- Original live DLL was backed up at `H:\Enshrouded_LiveBackup_20260928_panic_safe_proxy`.
- A fresh game session launched with the stable Mod Hub and produced normal EML startup records without a panic or loader error.
- The game process stopped cleanly after the smoke test.
- A later release rebuild containing the logging fallback produced another fresh stable-profile session without panic or loader error.

## Boundary

This prevents loader initialization errors from becoming fatal Rust panics. It does not make an invalid mod functional; invalid modules remain excluded from the stable profile and must be corrected or quarantined.

The proxy still contains one deliberate fail-fast boundary for a missing system `dinput8.dll` export. The forwarded exports do not all share one ABI, so replacing a missing export with a generic no-op would be unsafe. This is separate from EML startup failure handling and should be addressed only with typed per-export fallbacks or safe export omission.
