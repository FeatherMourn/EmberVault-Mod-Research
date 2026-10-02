# F7 Admin / Cheat Action Coverage Audit Report

Date: 2026-09-18  
Game Build / Revision: 1076226 (SHA-256 `af2f5a12...`)  
Status Policy: Every F7 action must end in exactly one of `IMPLEMENTED_AND_VERIFIABLE`, `IMPLEMENTED_UNVERIFIED`, or `UNSUPPORTED`. No implicit fallthrough. Any unsupported action must be visibly disabled in the UI.

---

## 1. Machine-Readable Action Coverage Table

| UI Action / Identifier | Routed Action | Backend System | Required Capability | Readback Available | Verification Status | Notes |
|---|---|---|---|---|---|---|
| `cheat.godmode.toggle` | `cheat.godmode.toggle` | Native Trampoline Hook | `healthHookReady` | Yes (health hook intercept) | `IMPLEMENTED_AND_VERIFIABLE` | Hook currently held OFF in Phase A |
| `player.health.fill` | `cheat.health.fill` | Native Trampoline Hook | `healthHookReady` | Yes (one-shot refill tick) | `IMPLEMENTED_AND_VERIFIABLE` | Bounded 2000ms expiry window |
| `cheat.mana.toggle` | `cheat.mana.toggle` | Native Trampoline Hook | `manaHookReady` | Yes (mana hook intercept) | `IMPLEMENTED_AND_VERIFIABLE` | Hook currently held OFF in Phase A |
| `player.mana.fill` | `cheat.mana.fill` | Native Trampoline Hook | `manaHookReady` | Yes (one-shot refill tick) | `IMPLEMENTED_AND_VERIFIABLE` | Bounded 2000ms expiry window |
| `cheat.stamina.toggle` | `cheat.stamina.toggle` | Native Trampoline Hook | `staminaHookReady` | Yes (stamina hook intercept) | `IMPLEMENTED_AND_VERIFIABLE` | Hook currently held OFF in Phase A |
| `player.stamina.fill` | `cheat.stamina.fill` | Native Trampoline Hook | `staminaHookReady` | Yes (one-shot refill tick) | `IMPLEMENTED_AND_VERIFIABLE` | Bounded 2000ms expiry window |
| `movement.speed` / `cheat.speed.set` | `cheat.speed.set` | Native Trampoline Hook | `movementHookReady` | Yes (movement hook accumulator) | `IMPLEMENTED_AND_VERIFIABLE` | Clashed via legacy RAX clobber; fixed via FF 25 detour |
| `movement.jump_height` / `cheat.jump.set` | `cheat.jump.set` | Native Trampoline Hook | `jumpHookReady` | Yes (jump hook intercept) | `IMPLEMENTED_AND_VERIFIABLE` | Hook currently held OFF in Phase A |
| `cheat.freecraft.toggle` | `cheat.freecraft.toggle` | Native Trampoline Hook | `craftHookReady` | No (< 14-byte hook site) | `UNSUPPORTED` | Overwrite length 12 bytes; fails closed until near relay proven |
| `cheat.skills.set` | `cheat.skills.set` | Native Trampoline Hook | `skillsHookReady` | Yes (skills hook intercept) | `IMPLEMENTED_AND_VERIFIABLE` | Hook currently held OFF in Phase A |
| `world.time_of_day` / `cheat.time.set` | `cheat.time.set` | Native Trampoline Hook | `daytimeHookReady` | Yes (daytime hook write) | `IMPLEMENTED_AND_VERIFIABLE` | Clashed via legacy RAX clobber; fixed via FF 25 detour |
| `world.time_pause` / `cheat.time.toggle` | `cheat.time.toggle` | Native Trampoline Hook | `daytimeHookReady` | Yes (daytime hook write) | `IMPLEMENTED_AND_VERIFIABLE` | Hook currently held OFF in Phase A |
| `cheat.item.reroll` | `cheat.item.reroll` | Native Probe Capture | `inventoryMoveHookInstalled` | Yes (memory readback `+8`) | `IMPLEMENTED_AND_VERIFIABLE` | Uses validated RVA `0x388453` probe capture |
| `survival.shroud` / `cheat.shroud.toggle` | `cheat.shroud.toggle` | Native Direct Byte-Patch | `patchShroudReady` | Yes (immediate readback) | `IMPLEMENTED_AND_VERIFIABLE` | Hardened safe patch with expected-byte gate |
| `item.durability` / `cheat.durability.toggle` | `cheat.durability.toggle` | Native Direct Byte-Patch | `patchDurabilityReady` | Yes (immediate readback) | `IMPLEMENTED_AND_VERIFIABLE` | Hardened safe patch with expected-byte gate |
| `movement.fall_damage` / `cheat.falldamage.toggle` | `cheat.falldamage.toggle` | Native Direct Byte-Patch | `patchFallDamageReady` | Yes (immediate readback) | `IMPLEMENTED_AND_VERIFIABLE` | Hardened safe patch with expected-byte gate |
| `survival.oxygen` / `cheat.oxygen.toggle` | `cheat.oxygen.toggle` | Native Direct Byte-Patch | `patchOxygenReady` | Yes (immediate readback) | `IMPLEMENTED_AND_VERIFIABLE` | Hardened safe patch with expected-byte gate |
| `survival.warmth` / `cheat.cold.toggle` | `cheat.cold.toggle` | Native Direct Byte-Patch | `patchColdReady` | Yes (immediate readback) | `IMPLEMENTED_AND_VERIFIABLE` | Hardened safe patch with expected-byte gate |
| `combat.parry` / `cheat.parry.toggle` | `cheat.parry.toggle` | Native Direct Byte-Patch | `patchParryReady` | Yes (immediate readback) | `IMPLEMENTED_AND_VERIFIABLE` | Hardened safe patch with expected-byte gate |
| `cheat.skills.reset` | `cheat.skills.reset` | Native Direct Byte-Patch | `patchSkillResetReady` | Yes (immediate readback) | `IMPLEMENTED_AND_VERIFIABLE` | Hardened safe patch with expected-byte gate |
| `build.altar_area` / `cheat.world.altar_area` | `cheat.world.altar_area` | Native Direct Byte-Patch | `patchAltarAreaReady` | Yes (immediate readback) | `IMPLEMENTED_AND_VERIFIABLE` | Hardened safe patch with expected-byte gate |
| `build.altar_far` / `cheat.world.altar_far` | `cheat.world.altar_far` | Native Direct Byte-Patch | `patchAltarFarReady` | Yes (immediate readback) | `IMPLEMENTED_AND_VERIFIABLE` | Hardened safe patch with expected-byte gate |
| `build.build_range` / `cheat.world.build_range` | `cheat.world.build_range` | Native Direct Byte-Patch | `patchBuildRangeReady` | Yes (immediate readback) | `IMPLEMENTED_AND_VERIFIABLE` | Hardened safe patch with expected-byte gate |
| `cheat.world.plant_growth` | `cheat.world.plant_growth` | Native Direct Byte-Patch | `patchPlantGrowthReady` | Yes (immediate readback) | `IMPLEMENTED_AND_VERIFIABLE` | Hardened safe patch with expected-byte gate |
| `glider.stamina` / `cheat.world.glider_stamina` | `cheat.world.glider_stamina` | Native Direct Byte-Patch | `patchGliderStaminaReady` | Yes (immediate readback) | `IMPLEMENTED_AND_VERIFIABLE` | Hardened safe patch with expected-byte gate |
| `cheat.stealth.toggle` | `cheat.stealth.toggle` | Native Direct Byte-Patch | `patchStealthReady` | Yes (immediate readback) | `IMPLEMENTED_AND_VERIFIABLE` | Hardened safe patch with expected-byte gate |
| `cheat.survival.enable_all` | `cheat.survival.enable_all` | Native Compound Action | `patch*Ready` | Yes (individual patch readback) | `IMPLEMENTED_AND_VERIFIABLE` | Enforces safe patch API on each member |
| `cheat.survival.disable_all` | `cheat.survival.disable_all` | Native Compound Action | `patch*Ready` | Yes (individual revert readback) | `IMPLEMENTED_AND_VERIFIABLE` | Enforces safe revert API on each member |
| `movement.autorun` | None (Client Simulated) | PowerShell UI Input | Keyboard Simulation | No (UI simulation only) | `IMPLEMENTED_UNVERIFIED` | Uses client Windows Forms input loop |
| `movement.hover` / `glider.flying` | None | None | None | None | `UNSUPPORTED` | C# AOB scanning unproven; disabled |
| `movement.gravity` | None | None | None | None | `UNSUPPORTED` | C# AOB scanning unproven; disabled |
| `glider.speed_mul` / `glider.lift_mul` | None | None | None | None | `UNSUPPORTED` | No native backend; disabled |
| `item.autoloot` | None | None | None | None | `UNSUPPORTED` | C# AOB scanning unproven; disabled |
| `item.clear` | None | None | None | None | `UNSUPPORTED` | No backend implementation exists; disabled |
| `item.give` | None | None | None | None | `UNSUPPORTED` | No inventory spawning backend; disabled |
| `crafting.recipe_unlock` | None | None | None | None | `UNSUPPORTED` | No recipe unlock backend; disabled |
| `gamesettings.production_time` | None | None | None | None | `UNSUPPORTED` | No production speed backend; disabled |
| `progression.player_level` | None | None | None | None | `UNSUPPORTED` | No player level backend; disabled |
| `progression.combat_xp` | None | None | None | None | `UNSUPPORTED` | No combat XP backend; disabled |
| `progression.xp_mul` | None | None | None | None | `UNSUPPORTED` | No XP multiplier backend; disabled |
| `build.instant_dismantle` | None | None | None | None | `UNSUPPORTED` | No instant dismantle backend; disabled |
| `terrain.flatten` | None | None | None | None | `UNSUPPORTED` | No terrain modification backend; disabled |
| `terrain.dig` | None | None | None | None | `UNSUPPORTED` | No terrain excavation backend; disabled |
| `prop.rotate` | None | None | None | None | `UNSUPPORTED` | No prop transformation backend; disabled |
| `prop.clone` | None | None | None | None | `UNSUPPORTED` | No prop duplication backend; disabled |
| `entity.kill` | None | None | None | None | `UNSUPPORTED` | No entity death trigger backend; disabled |
| `entity.despawn` | None | None | None | None | `UNSUPPORTED` | No entity removal backend; disabled |
| `player.recovery.set` | None | None | None | None | `UNSUPPORTED` | No continuous regen backend; disabled |
| `player.attributes.set` | None | None | None | None | `UNSUPPORTED` | No attribute scaling backend; disabled |
| `player.scaling.set` | None | None | None | None | `UNSUPPORTED` | No damage modifier backend; disabled |
| `player.recover_items` | None | None | None | None | `UNSUPPORTED` | No tombstone recovery backend; disabled |
| `cheat.teleport` / `travel.teleport` | `cheat.teleport` | Disarmed | None | None | `UNSUPPORTED` | ADM-TEST-0002 local player transform identity unsolved |
| `entity.teleport` | None | Disarmed | None | None | `UNSUPPORTED` | ADM-TEST-0002 local player transform identity unsolved |
| `travel.return_previous` | None | Disarmed | None | None | `UNSUPPORTED` | ADM-TEST-0002 local player transform identity unsolved |
| `multiplayer.player.teleport` | None | Disarmed | None | None | `UNSUPPORTED` | ADM-TEST-0002 local player transform identity unsolved |

---

## 2. Summary of Coverage

- **Total Distinct F7 Actions Audited**: 54
- **IMPLEMENTED_AND_VERIFIABLE**: 27 (11 hook-backed, 1 probe-backed, 13 direct byte-patch, 2 compound actions)
- **IMPLEMENTED_UNVERIFIED**: 1 (`movement.autorun`)
- **UNSUPPORTED**: 26 (All 26 must be visibly disabled in the F7 Admin Codex)
- **Fallthrough Guarantee**: No F7 action can dispatch to an unbacked or undefined handler. Any action without a verified backend fails closed immediately.
