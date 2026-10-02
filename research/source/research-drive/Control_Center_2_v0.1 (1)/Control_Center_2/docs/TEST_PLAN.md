# Staged verification plan

1. **READ-ONLY:** Re-index local KFC copies outside the KFC directory; record actual originating game build when independently known. Verify source fingerprints, inspect a registered vanilla item and its known producing recipe. Expected: stable GUID joins; no writes to source ZIPs.
2. **OBSERVE-ONLY:** With legacy Control Center disabled, manually test `probe_mod/CC2_Research_Probe` on a disposable setup after checking compatibility with installed EML. Record exact game build, EML version, startup log, capability availability, and resource query outcomes. Expected: either observed resource counts or useful failure logs. No resource mutation.
3. **REVIEW GATE:** Confirm installed EML's resource creation APIs, signature/calling conventions, lifecycle timing, schema for an existing resource and safe fail-closed behavior. If any are unknown, stop rather than generating a guessed mod.
4. **SINGLE-ITEM EXPERIMENT (future):** In a separate test mod and disposable world only, clone the verified vanilla resource graph with proposed new identity, initially reusing vanilla visuals; verify independent registration, crafting, knowledge/display and no modification to the source item. Record negative results.
5. **VISUALS (future):** Change one reference at a time: vanilla icon/model/material, then investigate actual custom binary asset support; compare KFC observations and runtime captures.
6. **SCALING (future):** Once one independent item is user-confirmed in-game, implement a reviewed resource factory and collision-resistant IDs. Only then extend to building blocks, furniture and other content classes.

**Promotion criteria:** KFC observations support static structure only; runtime claims require a matched-build capture or user-confirmed in-game result. Never enable unreviewed save-affecting or multiplayer modifications.
