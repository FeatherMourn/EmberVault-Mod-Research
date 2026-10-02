# Enshrouded Master Trainer — audited repair candidate

**Status:** PARTIAL / STATIC REPAIR ONLY. This is not a fully repaired or runtime-qualified trainer. Nothing was enabled in Enshrouded. Preserve the original file.

## Input and output
- Original: `Enshrouded_Master_Trainer.CT` (unchanged), SHA-256 `0a591301a96c5fdf257564dec6d53603eefec4ad7c79a3677bb7b3ecfa707d30`.
- Candidate: `Enshrouded_Master_Trainer_Audited_Candidate.CT`, SHA-256 `7c93e660610b3c6ed59eb26629a1ad14fae330fd686dd0e510e58a146fcedd7d`.
- Input: 161 Cheat Engine entries, 66 Auto Assembler scripts, 8 top-level groups. XML parsed successfully; no duplicate IDs.
- Candidate: 165 entries, 68 Auto Assembler scripts, 9 top-level groups. XML re-parsed and validated, with all 161 original entries retained.

## Changes made
1. Added a new top-level `[00] USER-TESTED HEALTH SCRIPTS` group with the two **separate** user-confirmed implementations from this conversation: Full Health and adjustable Damage Reduction. Full Health uses an AOB signature; Damage Reduction uses the **build-specific** direct hook `enshrouded.exe+364798` guarded by `assert`. They are not established to be player-only or compatible after a game update.
2. Added an editable `4 Bytes` child beneath Damage Reduction at `DamageTakenPercent`, default 50. Valid intended range 0–100; the child only resolves while its parent script is enabled. Value is **percent of damage taken**, not percentage reduced.
3. Renamed 30 legacy per-script `newmem` allocations and 21 legacy `mem_tp` allocations to distinct per-entry symbols to eliminate shared allocation-name collisions. No legacy patch bytes, AOB signatures, gameplay code, hierarchy, or child addresses were otherwise modified.
4. Marked 10 config-only stubs `[CONFIG ONLY: NO GAME HOOK]`; these allocate settings but do not implement the advertised gameplay features.
5. Clearly labeled the 21 teleport entries `[UNVERIFIED: REQUIRES FLIGHT POINTER]` because they depend on `pPlayerPos` from the separate gravity/free-fly entry.
6. Labeled the legacy God Mode script as overlapping the new Full Health script, and flagged the previously unmatched fall-damage AOB, hard-coded ammo call, and unverified gravity native hooks.

## What still needs actual repair / evidence
- **21 teleport scripts still have `createthread` allocations without corresponding deallocations.** They also share an unproven `pPlayerPos` source and mutate world/player position. Renaming their allocation symbols does **not** fix the leak or establish safe execution. Left unchanged rather than guessing at a thread lifetime or teleport authority.
- The legacy God Mode script intercepts the same health read as Full Health but applies a float multiplier to the value returned by the original read. Its label and real gameplay semantics are not independently validated. **Do not enable both at once.**
- The prior read-only reference audit of the executable (SHA-256 `AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`) found the exact legacy fall-damage signature had **zero** matches. The audit did not run the table. Other signatures can also fail or move in a different build.
- The ammo script contains a hard-coded absolute call (`0x1406284f0`) and hard-coded restoration bytes. The gravity/free-fly script calls a Windows function inside a hook without a demonstrated register/stack/lifetime contract. These were **not** modified or enabled.
- Other legacy scripts and child value records are **unverified**, even if they have matching AOB signatures. A unique pattern match is not gameplay proof.

## Static checks
- Input and output XML parse: PASS.
- All original CheatEntry IDs retained, none duplicated: PASS.
- All 68 scripts retain `[ENABLE]` and `[DISABLE]`: PASS.
- No duplicate `alloc()` symbol names across entries after repair: PASS.
- All original script text preserved exactly except the 51 local allocator-name substitutions: PASS.
- Compiling the Auto Assembler scripts: **NOT TESTED** (requires Cheat Engine and the exact loaded game build).
- Runtime gameplay, multiplayer, save integrity, and shutdown/unload: **NOT TESTED**.

## Safe starting point
1. Load the candidate `.CT` in Cheat Engine and save a separate copy. **Do not run the entire table**.
2. On the same executable where you already confirmed the features, test each entry in the new `[00]` group **one at a time**, in an expendable single-player world. The two entries come from your previously working scripts; the candidate itself has not been runtime-tested.
3. Keep the old legacy God Mode off whenever the new Full Health entry is active. Full Health can also mask the effect of Damage Reduction; test them separately.
4. To repair additional scripts rather than relabel them, provide the exact current `enshrouded.exe` (or its executable SHA-256 and relevant Memory Viewer disassembly) and identify the next features you want enabled. Avoid guessing replacement AOBs or transplanting absolute RVAs from another build.
