# INC-0062 — Architect Toolkit v0.42.0 deep dive

Date: 2026-09-20
Source: user-provided `architect_toolkit.zip`
SHA-256: `768ac907e33038d8a5efe4535ae1d3745abe4308de06a7d7694060068538b5ec`
Build identity: `0.42.0 / architect-v042-hotbar-0022b-crash-guard-20260920 / hybrid_observer_and_admin_mutation`
Status: SOURCE REVIEW / NOT CURRENT-DESIGNATED

## High-level conclusion

The latest source already contains a partially modernized F7 shell, source-consolidation work, Cheat Engine catalog preservation, CODE-0022B attribute research artifacts, and substantial fail-closed native work. The correct next step is **not** to rebuild F7 from scratch and **not** to add more cheat backends immediately.

The immediate repair sequence should be:

1. repair the canonical F7 action registry / control binding / truthfulness mismatch;
2. rebuild only the page-content layout layer around responsive WinForms containers;
3. migrate existing pages into the new 11-page product structure without changing backend semantics;
4. replace stale source-pattern truthfulness tests with behavior/registry-bound tests only after every executable control has a canonical action ID;
5. keep crash-guarded/unproven CODE-0022B attribute hooks disarmed while exposing planned editable fields truthfully disabled;
6. runtime smoke the UI before any new player/loot/Lua mutation research resumes.

## Current F7 shell

`runtime/ArchitectRuntime.ps1` already creates a separate sizable F7 WinForms form with:

- `FormBorderStyle = Sizable`
- minimum/default dimensions
- Docked top header
- Docked left navigation rail
- Docked fill body/content
- `AutoScroll` on the main content panel
- saved/restored window bounds

Therefore the user's resize complaint is **not an outer-window problem anymore**.

### Actual resize defect

All F7 page renderers still use fixed pixel coordinates and fixed-width panels/controls through:

- `New-Label(Text, X, Y, W, H, ...)`
- `New-Panel(X, Y, W, H, ...)`
- `New-Button(Text, X, Y, W, H, ...)`
- direct `.Location = Point(...)`
- direct `.Size = Size(...)`

There are zero `TableLayoutPanel`, zero `FlowLayoutPanel`, and zero `DataGridView` references in the current F7 runtime page code.

Most primary page panels are approximately 590–700 px wide. Expanding the form therefore increases the content viewport but not the actual page content, leaving controls clustered in the upper-left.

The existing `tests/test_ui_smoke.ps1` does resize the form at five resolutions, but its layout assertion only verifies that the outer Header is Dock=Top and Main is Dock=Fill. It does **not** verify that page sections expand, reflow, avoid clipping, or consume available width. This explains why the current smoke suite can pass while the user-visible resize bug remains.

## Current navigation

Current F7 nav entries:

1. Dashboard
2. Player Vitals
3. Character Sheet
4. Player Attributes & Stats
5. Mobility
6. Inventory & Crafting
7. World Settings
8. Multiplayer & Quests
9. Source Map
10. CT Catalog
11. Enshrouded Wiki (external browser action)
12. Settings & Dev

This does not yet match the newly approved product grouping:

1. Home
2. Player
3. Mobility & Navigation
4. Items & Progression
5. Combat & AI
6. World & Environment
7. Building & World Editing
8. Entities & Authority
9. Camera & Presentation
10. Mods & Configuration
11. Developer & Diagnostics

`Source Map` and `CT Catalog` should be retained but nested under Developer & Diagnostics rather than thrown away.

## Current external-source consolidation work

The source already contains:

- `runtime/source_consolidation_catalog.json`
- `docs/research/CODE-0040_external_source_consolidation.md`
- `runtime/cheat_table_1013216_catalog.json`

The CT catalog preserves all 224 entries/groups/children for `enshrouded_1013216.CT` as metadata. The source-consolidation catalog currently defines 15 deduplicated families across six external artifacts.

This work should be preserved and reused as provenance behind the new F7 capability matrix. Do not duplicate it.

## Current action-registry blocker

The most important code-architecture issue is documented by CODE-0037C/D/E and confirmed in source.

`runtime/ArchitectRuntime.ps1` initially constructs a larger compatibility ledger containing many Player/Item actions, but later replaces `$adminCommandRegistry` with `runtime/admin_action_registry.json`.

The JSON registry currently has only 20 actual `actions`, mostly diagnostic/read-only actions plus three disabled item actions. Many visible F7 mutation routes exist only in UI closures, capability aliases, or `actionFamilies`, not as canonical action entries.

Consequences:

- `Register-SafeUiEvent` has no canonical `ActionId` parameter.
- Many clickable controls have no stable action metadata in `Tag` or another map.
- Existing truthfulness tests cannot reliably map a visible control to its canonical action/backend.
- CODE-0037C/D/E correctly stop rather than guessing action IDs.
- Current latest verification is 162/163 invariants because the F7 Truthfulness & Safety Contract suite remains unqualified.

This registry/binding issue should be repaired **before or as the first step of the responsive F7 refactor**, otherwise the UI rewrite will reproduce the same action identity ambiguity in a prettier layout.

## Current status/truthfulness issues to preserve or repair

### CODE-0022B attribute observer

`Render-PlayerAttributesPage` still presents `ARM HOOKS`, `DISARM HOOKS`, and `REFRESH`.

However:

- current build ID explicitly includes `0022b-crash-guard`;
- `docs/research/CODE-0040_external_source_consolidation.md` states the 27-stat arm path caused repeated access violations / toolbar crash and remains disarmed;
- native `PlayerAttributeObserver.c` immediately returns failure while `SEMANTIC_PLAYER_ATTRIBUTE_OBSERVER_READY` is false;
- native runtime logs a crash-guard rejection;
- PowerShell `Publish-PlayerAttributeDiscoveryCommand` still reports the ARM request as queued/accepted before native rejection.

The responsive/UI refactor should therefore remove or disable the live ARM affordance and present the 27 stats as crash-guarded research/planned-edit controls until a new independently qualified observer exists. Do not reconnect writable Attributes/Derived Stats to this old hook path.

### Direct UI-local mutation state

Several page handlers still assign `NativeMemoryEngine` properties directly (recovery multipliers, damage/crit/attack speed, weapon scaling, player level, XP multiplier, glider descent/turn, resource yield, loot multiplier, altar limit, build reach, etc.) and immediately publish success-like status text. Current code later disables many containing panels, but the architecture still contains these UI-local mutation pathways.

The new UI should not carry these patterns forward. Every executable setting must bind to one canonical action/capability definition and derive availability/result from that backend contract. Unsupported controls may render but must be disabled.

### Auto Loot inconsistency

Source consolidation says Architect's QoL startup resource path remains the sole auto-loot owner and the live F7 toggle must not simulate pickup. `Send-CheatCommand` correctly rejects `cheat.autoloot.toggle` as `STARTUP_CANARY_ONLY`.

`Get-AdminCapabilities`, however, currently contains an `autoLoot` capability that says executable/ready. This should be reconciled so UI capability metadata agrees with the actual command path and current source-consolidation policy.

### Stale evidence/metadata inside registry families

Some `actionFamilies` contain historical or over-broad statuses/reasons that conflict with higher-authority current evidence. Example: the Travel family claims a validated direct player-coordinate write, while current project/native policy deliberately disarms teleport because local-player transform ownership is unresolved. Do not promote family-level metadata to executable truth without reconciling against current capability/negative evidence.

## Tests

Useful existing suites should be preserved:

- native compilation
- C# compilation
- PowerShell AST
- CODE-0036/0037 regression
- command routing
- direct patch integration
- patch engine lifecycle
- hook transparency
- Site A probe lifecycle
- patch readiness
- teleport disarmament
- hook-off baseline
- headless WinForms smoke

But `tests/test_ui_smoke.ps1` needs real responsive-layout assertions. New tests should inspect every page at multiple client widths/heights and assert, at minimum:

- main page root fills available client area;
- section containers resize/reflow rather than stay fixed at ~700 px;
- no enabled visible control extends beyond its page container without scroll support;
- minimum-size layout has no overlap among sibling controls;
- larger layouts consume additional horizontal width;
- datasets use actual grids/list containers with fill behavior;
- navigation itself remains usable;
- all executable controls have canonical action IDs and canonical capability definitions.

`tests/test_f7_truthfulness.ps1` should not be bulk-rewritten until canonical UI-action binding exists. After that binding exists, replace brittle source-pattern assertions with behavioral/metadata assertions.

## Recommended first Codex scope

First task should be a combined **F7 action-binding repair + responsive shell/page-layout refactor**, not new gameplay features.

Allowed:

- expand/normalize canonical `admin_action_registry.json` to include every existing F7 executable control/action as truthful metadata, without enabling anything new;
- create a single ActionId -> Control binding/registry used by UI and tests;
- extend `Register-SafeUiEvent` or add an adjacent binding helper so canonical action identity is explicit;
- introduce `TableLayoutPanel`/`FlowLayoutPanel` based reusable responsive sections/rows;
- migrate current F7 pages into the new 11 product pages;
- move Source Map/CT Catalog under Developer & Diagnostics;
- add disabled placeholders for newly approved Player writable Attributes/Derived Stats and Mods & Configuration features, but no new mutation backend;
- strengthen resize and truthfulness tests.

Not allowed in first task:

- re-enable CODE-0022B crashy hooks;
- add guessed offsets/signatures/pointers;
- create new player/stat writes;
- implement arbitrary Lua editor execution;
- implement live auto-loot, teleport, terrain/prop mutation, multiplayer/quest mutation;
- redesign F8 or native backend architecture;
- designate this intake as Architect_Mod/Current without explicit user approval.

## Runtime acceptance test for the first refactor

1. Start Enshrouded on build 1076226 in a safe test world.
2. Open F7 and visit all 11 product pages.
3. Resize continuously from minimum size through 1280x720, 1600x900, and maximized.
4. Verify sections reflow/expand and do not remain pinned in the upper-left.
5. Verify no overlap/clipping; scrolling appears only when needed.
6. Verify lists/grids use available width.
7. Verify unsupported/crash-guarded actions are disabled and explain why.
8. Verify Source Map and CT Catalog remain accessible under Developer & Diagnostics.
9. Exercise one safe/read-only existing action and verify ACK/history/status.
10. Open F8 and verify behavior is unchanged.
11. Close/reopen F7 and verify bounds/layout persistence.
12. Clean shutdown and inspect `ui_errors.log`.

Compilation/offline tests do not promote the UI to runtime-proven; user in-game confirmation is required.
