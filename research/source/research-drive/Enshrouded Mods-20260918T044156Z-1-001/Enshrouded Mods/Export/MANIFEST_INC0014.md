# Architect Toolkit INC-0014 Test Build Manifest

Build Date: 2026-09-18
Game Build/Revision: 1076226 (SHA-256 af2f5a12...)
Architect Runtime Version: 0.33.0 (INC-0014 ADM-TEST-0002 Teleport Disarmament)
Source Archive: architect_toolkit.zip
Source Archive Bytes: 39653864
SHA-256: 85669af9509dafedd5b93347ababf45e9de2ff229e5fa8642ed217f4e9cb3503
Native Runtime DLL SHA-256: ddc016bcaaac7c3551ab8beb07fe00de51e77ddada65396e308d2559af441202

Status: OFFLINE_QUALIFIED (INC-0014 Resolved — Unsafe Teleport Path Disarmed)

Incident Summary (ADM-TEST-0002):
In-game testing identified that native hook RVA 0x2C6863 (architect_cheat_transform_entry) unconditionally
captured RDX at startup without local player identity validation, causing corrupted entity coordinate
writes during world loading.

Remediation Verification Summary:
- RVA 0x2C6863 Disarmed: Native runtime does NOT hook 0x2C6863 at startup; g_cc.transformInstalled is FALSE.
- Hook Capability Requirement: CheatCorrelationHarness.c lowered required hook count from 9 to 8.
- Zeroed Globals: g_teleportPending, g_targetPosX/Y/Z, and g_pPlayerTransform zeroed on init and end.
- Native Fail-Closed: parse_cheat_correlation_command rejects 'cheat.teleport' with ok = FALSE.
- C# Memory Disarmed: NativeMemoryEngine.WritePlayerCoordinates() unconditionally returns false.
- Bridge Fail-Closed: Invoke-PlayerTeleport disarmed and Send-CheatCommand / Dispatch-AdminCommand reject teleport actions fail-closed.
- F7 UI Disabled: Warp, Custom Warp, Safe Spawn, Waypoint Hub Teleport, Entity Teleport, and Return Previous buttons are disabled and labeled UNSUPPORTED.
- Automated Test Validation:
  * PowerShell AST Syntax: 4/4 scripts passed with 0 syntax errors
  * C# Dynamic Compilation: PASS (0 errors)
  * Pipeline Regression Suite: 10 / 10 PASS
  * Stale Command & Mutation Boundaries: 6 / 6 PASS
  * ADM-TEST-0002 Suite: 15 / 15 PASS
