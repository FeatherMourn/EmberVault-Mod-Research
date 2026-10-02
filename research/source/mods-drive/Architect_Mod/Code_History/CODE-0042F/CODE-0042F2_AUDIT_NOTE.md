# CODE-0042F2 — Closure strategy correction

Date: 2026-09-20
Build scope: Enshrouded 1076226
Status: PLANNED NEXT STEP / NO RUNTIME CLAIM

Current static source measurement:
- 48 direct `Register-SafeUiEvent` call sites file-wide
- 58 direct `.Add_Click(...)` registrations file-wide
- 106 total raw event-registration call sites file-wide

The 106 figure is not the F7 denominator. It includes registration-helper internals and F8-only handlers. Previous source audit estimates the defined F7 surface at approximately 96 raw registrations after excluding those categories.

A single all-at-once closure request has proven too large. The next implementation should use bounded page batches while preserving one stable event-inventory architecture.

Recommended sequence:
- G1: lifecycle/identity infrastructure + F7 shell + Home + Player + Mobility
- G2: Items + Crafting/Progression + Combat + World/Camera + Building
- G3: Settings + Multiplayer/Quests + Codex + Map/Wayfinder + Blueprint Browser + remaining F7 subviews/dialogs
- G4: full-F7 static closure proof + repeated 11-page traversal + zero-gap audit

Responsive page migration remains deferred until G4 is green.
