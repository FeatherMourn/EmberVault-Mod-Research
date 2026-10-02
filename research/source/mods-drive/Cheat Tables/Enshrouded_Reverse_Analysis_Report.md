# Enshrouded independent reverse-analysis report

## Scope

This is a static-only analysis of `H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe`. The requested F: table paths were not accessible. Existing CT files were not used as a source for code, symbols, AOBs, offsets, or hooks.

## Executable identity

- SHA-256: `AF2F5A1227911D8AA06B3908D6BD021183821CAE14EA91099CB57D0DF990781`
- Image base: `0x140000000`
- Entry RVA: `0x2D6D310`
- `.text`: RVA `0x1000`, virtual size `0x12A5080`
- `.rdata`: RVA `0x12A7000`, virtual size `0xC36D40`
- PE sections: `.text`, `.rdata`, `.data`, `.pdata`, `_RDATA`, `.rsrc`, `.reloc`, `.bind`

## Static triage result

The independent Capstone/PE parser found 1,918 printable `.rdata` strings containing one or more requested feature terms. It found zero direct RIP-relative `.text` references into those string spans. This means string vocabulary does not identify the health, stamina, mana, XP, durability, fall, movement, jump, timer, or crafting implementation in this build.

No address, offset, pointer, AOB, or hook was inferred from this result.

## Feature status

Health, stamina, mana, XP, durability, fall damage, movement speed, jump height, shroud, oxygen, body heat, and crafting cost: **Needs evidence**.

For each feature, the missing evidence is a controlled offline runtime scan followed by repeated action-triggered access/write traces, register/operand capture, structure/data-flow classification, and current-build AOB uniqueness verification. No game process was running during this analysis, so those traces could not be collected.

## Required next evidence

1. Start the game offline with a backed-up disposable save.
2. Record a baseline value for one feature only.
3. Change that value through normal gameplay and scan for the exact data type.
4. Repeat the same action several times and capture reads and writes.
5. Distinguish authoritative gameplay state from cached/UI/temporary values.
6. Save original bytes, verify full instruction boundaries, and derive a new signature only after the target is proven.
7. Validate exactly one match in the current executable and test enable/disable/reload/edge cases.

Until that evidence exists, the independent table must remain infrastructure-only for these features. Assembly success or a candidate string is not functional proof.
