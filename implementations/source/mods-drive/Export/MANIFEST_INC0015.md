# Architect Toolkit INC-0015 Test Build Manifest

Build Date: 2026-09-18
Game Build/Revision: 1076226 (SHA-256 af2f5a12...)
Architect Runtime Version: 0.34.0 (INC-0015 Hook-Off Diagnostic Build)
Source Archive: architect_toolkit.zip
Source Archive Bytes: 39653609
SHA-256: 72255e64b6c7bd2e3ac218cd565926eb90103dd83129d5d06515cd6f5c856a7b
Native Runtime DLL SHA-256: 86b0b16496f88d8c2fd59405b53c66342d86dfb32ed6fa62b7c8f86e6e3cb665

Status: OFFLINE_QUALIFIED (INC-0015 Diagnostic Hook-Off Ready)

Incident Summary (ADM-TEST-0003):
Root cause identified: `write_abs_jump()` destroys `RAX` (`mov rax, <hook> / jmp rax`). At RVA 0x23AE34
(movement hook), displaced `add rcx, rax` received the 64-bit hook entry address, adding an enormous
pointer-sized value into `[rdx]` (the game's movement accumulator) and launching the player out of the
map at startup even when Super Speed was OFF. Similar corruption occurred at 0xCE518A (daytime).

Diagnostic Build Verification Summary:
- Startup begin removed: `cheat_correlation_initialize()` initializes state only; zero cheat hooks installed at startup.
- Dispatch auto-begin removed: `parse_cheat_correlation_command()` does NOT auto-invoke `cheat_correlation_begin()`.
- Zero Trampoline Hooks: On DLL load and world spawn, zero cheat-correlation trampolines are installed.
- Teleportation Disarmed: All INC-0014 fail-closed protections (RVA 0x2C6863 unhooked, WritePlayerCoordinates returns false, F7 UI disabled) remain in effect.
- Automated Test Validation:
  * PowerShell AST Syntax: 4/4 scripts passed with 0 syntax errors
  * C# Dynamic Compilation: PASS (0 errors)
  * Pipeline Regression Suite: 10 / 10 PASS
  * Stale Command & Mutation Boundaries: 6 / 6 PASS
  * ADM-TEST-0002 Suite: 15 / 15 PASS
  * INC-0015 Hook-Off Verification: 3 / 3 PASS
