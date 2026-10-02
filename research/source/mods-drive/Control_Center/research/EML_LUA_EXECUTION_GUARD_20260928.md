# EML Lua execution guard — 2026-09-28

## Change

`crates/mod-loader-lua/src/runner/mod.rs` now installs a per-mod Lua
instruction hook before execution and removes it afterward. If a module spends
30 seconds in Lua instructions, the runner returns a recoverable runtime error
identifying that module instead of allowing unbounded Lua execution.

This guard does not claim to interrupt a native engine call that itself blocks;
those calls require bounded EML asset APIs and remain separately classified.

## Verification

- `cargo check -p mod-loader-lua` passed.
- `cargo test -p mod-loader-lua` passed.
- Release `dinput8-proxy` build passed.
- Installed proxy SHA-256:
  `F5D255B71DC6721FF074001D39F2FE51EFF23484F0434CFDC8549017C67B5262`
- Previous live DLL backup:
  `H:\Enshrouded_ControlCenter_Backups\runtime_lua_timeout_20260928-060216`
- Fresh Steam smoke report:
  `research/live_runtime_smoke_after_lua_timeout_proxy_20260928.json`

The fresh session loaded the expected build, ran `enshrouded_mod_hub`, applied
1910 patches, and attached the runtime loader without a panic or mod error.
