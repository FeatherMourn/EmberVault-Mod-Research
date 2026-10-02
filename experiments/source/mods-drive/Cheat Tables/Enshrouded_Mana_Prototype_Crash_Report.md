# Mana prototype crash report

## Evidence

Crash archive: `H:\SteamLibrary\steamapps\common\Enshrouded\crash_dumps\enshrouded_20260925_090424.zip`

- Exception: `ILLEGAL_INSTRUCTION`
- Process ID: `22012`
- Executable module base in dump: `0x7FF6B19D0000`
- Call stack includes `0x7FF6B1BC3017`, which is the instruction immediately after the prototype hook site at `0x7FF6B1BC3014`.
- The live bytes at the hook site were independently read as `89 04 99 48 83 EF 10` before the crash.

## Decision

The prototype is **Unsafe to re-enable pending correction**. Do not use it on a live save or with the master trainer active.

The crash is not evidence that the Mana address or static routine is wrong. It indicates that the injected trampoline/return path was not safe in the actual runtime context, or that another active patch/mod interacted with it. The dump does not by itself identify which instruction generated the illegal instruction.

## Immediate containment

1. Close the game and Cheat Engine.
2. Do not re-enable `Enshrouded_Mana_Independent_Prototype.CT`.
3. Start the game without the prototype and verify the executable is unmodified before further testing.
4. Test only with the master trainer and other code-injecting mods disabled.

## Required correction gate

Before any replacement prototype is tested, validate the assembled trampoline bytes, jump destination, return address, and instruction boundaries in a suspended disposable process. The replacement must use an independently verified near allocation, preserve all live state, and prove clean disable/restore. No Mana override should be added until this gate passes.
