# Architect Toolkit INC-0013 Test Build Manifest

Build Date: 2026-09-18
Game Build/Revision: 1076226 (SHA-256 af2f5a12...)
Architect Runtime Version: 0.32.0 (INC-0013 Architecture Unification)
Source Archive: architect_toolkit.zip
Source Archive Bytes: 39655671
SHA-256: ea356db664c771d6c334268789841b7996a65dc51762f0388da5de611b9908c8

Status: OFFLINE_QUALIFIED (INC-0013 Resolved)

Verification Summary:
- Elimination of RVA 0x388453 collision (single probe services inventory move and reroll)
- Single mutation ownership: C# yields write access to native DLL at all mutation boundaries
- Exact build SHA-256 validation gate enforced in NativeMemoryEngine.Attach()
- Stale command replay prevention via .last_processed_command.id persistence and startup purge
- Bounded 2000ms lifecycle timeout on one-shot vitals replenishment flags
- Signed 64-bit teleport coordinate parsing (json_get_i64)
- F7 UI disabled/flagged unsupported buttons and truthful 'queued' state reporting
- F8 HUD truthful 'live_refresh_unproven' carrier equipping reporting
- Compiled with MSVC x64 (ArchitectNativeRuntime.dll SHA-256 fb4336db2badc4fe0a77a184440dbdd9f1f77d0a24106404bc46fe3187cc9631)
