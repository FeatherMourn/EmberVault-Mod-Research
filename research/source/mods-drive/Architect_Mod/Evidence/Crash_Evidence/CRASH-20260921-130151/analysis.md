# CRASH-20260921-130151 — Enshrouded save-load crash analysis

Status: EXPERIMENTAL / evidence report (not a canonical conclusion)
Date analyzed: 2026-09-21
Source intake: INC-0063
Crash package SHA-256: 477d289ddd73a73515c9b36c286f25be4abb06d30852abea8721153ba8c122f8

## PROVEN from dump/log

- Exception: 0xC0000005 ACCESS_VIOLATION, read from address 0x34.
- Faulting instruction: enshrouded.exe RVA 0xE9AC32.
- Executable module base: 0x7FF78DA70000; image size 0x02DA7000; PE timestamp 0x6A4236C8.
- At RVA 0xE9AC32 the instruction is `movzx ebx, byte ptr [rdx+r14+0x28]`.
- R14 is zero at the fault. The local index in EDX is 12, so the effective read is 0 + 12 + 0x28 = 0x34, exactly matching the exception parameter.
- The crashing function begins at RVA 0xE9ABD0 and preserves its original second argument in R14; therefore the game function was called with a null second-argument pointer and dereferenced it.
- The coordinate argument recovered from R8 points to three 32-bit values: (8480, 1080, 6880). The function maps them to a 4x4x4 local-cell index; the failing index is 12.
- Save deserialization completed successfully: save version 12, 9 bases, 4,818 entities; server entered Run. Client initialization reached Systems Ready and SyncCharacterSaveGame, then logged `Received new Character save game` immediately before the crash window.
- This is not the logged Vulkan-device-lost failure pattern and the dump does not show memory exhaustion.
- Loaded third-party modules include Shroudtopia loader modules plus flight_mod.dll, ChatCommands.dll, and whitelist_mod.dll.
- ArchitectNativeRuntime.dll is not present in the dump module list. Thus Architect's injected native DLL startup hooks were not loaded in this crashing process.

## INFERRED

- The faulting routine is strongly consistent with a voxel/world-local lookup: it maps x/y/z coordinates into a 0..63 cell index and reads a byte table from the second-argument object at +0x28. Exact subsystem/type name remains UNSOLVED without matching executable disassembly/symbols.
- The immediate trigger is therefore a missing/null world/voxel-side object reaching a vanilla function, not a direct crash inside ArchitectNativeRuntime.dll.
- Architect's EML/Lua resource mutation remains a possible upstream cause because it can be active through the mod loader without appearing as its own DLL module.
- The other loaded native mods are also upstream candidates. Public Shroudtopia release notes show Flight/Basic mods were specifically updated for older SVN revisions, describe ChatCommands as extremely unstable, and previously marked Whitelist Mod broken. They must be isolated before attributing this crash to Architect resource data.

## Discriminating test order

1. Disable Flight Mod, ChatCommands, and Whitelist Mod while leaving the loader present. Launch the same save without pressing F7 / injecting ArchitectNativeRuntime.dll.
2. If it still crashes at RVA 0xE9AC32, disable Architect's EML/Lua mod layer and retry the same save.
3. If clean with Architect EML disabled, reproduce with a play-safe Architect Lua mode that returns before any resource mutation, then re-enable resource mutations by group to identify the first bad mutation.
4. If it crashes even with all mods/resource mutations disabled, treat as vanilla/save/world evidence and capture the clean crash dump for comparison.

## Safety

Do not patch RVA 0xE9AC32 with an invented null guard yet. The correct null-case semantics are not known, and masking the dereference could turn a deterministic crash into world/save corruption. Map the caller and expected second-argument object first.
