# Independent Mana prototype

Status: **Ready for testing** as a diagnostic pointer capture; not a Mana override.

Evidence:

- User-confirmed scan address: `0x3006EF1EFA4`.
- Casting reduces the value and regeneration restores it to `365`.
- Primary writer: `enshrouded.exe+0x1F3014`, bytes `89 04 99`, `mov [rcx+rbx*4],eax`.
- Captured post-write registers: `RCX=0x3006EF1EFA4`, `RBX=0`, `EAX=365`.
- Independently derived 24-byte routine-entry AOB matches exactly once at RVA `0x1F2F50`.
- Write-site displacement from routine entry: `0xC4`; the assertion context begins at `0xBA`; the patch covers 7 complete bytes: `mov` plus `sub rdi,10`.

The prototype stores `RCX` only when `RBX==0`, replays the overwritten instructions, and does not alter Mana. It has complete symbol and allocation cleanup. Pointer validity across reload/respawn remains a live-test question.

Offline test:

1. Back up a disposable save and attach to the recorded executable build.
2. Enable the diagnostic script without changing the captured pointer.
3. Cast the same spell repeatedly and observe `manaPtr`.
4. Confirm Mana decreases and refills normally.
5. Reload/respawn and confirm pointer recapture or safe failure.
6. Disable the script and verify original bytes, symbols, and allocations are restored.

Risks: code injection and pointer capture can crash if the executable differs or the signature is not unique. Offline/local testing only; no multiplayer or save mutation.
