# Control Center milestone 1 capability report

## Verified now

- EML can register a cloned ItemInfo resource at runtime.
- Donor resources can remain untouched while a new item ID is assigned.
- The stable furniture fixture can clone a recipe and add a visible crafting
  slot by cloning the containing UI recipe set.
- Fixed-size UI arrays require typed-entry replacement inside a cloned set;
  direct append to set.entries is unsafe.
- Compiled projects can record recipe/UI plans and asset-substitution plans.
- Generated probes have unique IDs, fresh-session evidence markers, rollback
  backups, and stale-log classification.
- The Control Center test suite passed 485 tests in the latest verification run
  (the earlier milestone snapshot recorded 303 tests).
- Offline builder catalogs support JSON import, search, tags, favorites,
  material totals, and portable build plans; these utilities do not mutate
  game state.
- Gameplay feasibility planning conservatively labels custom interactions and
  broader AI/quest/animation/world-generation work as research-only, while
  multiplayer authority remains unsupported.

## Experimental

- Scalar ItemInfo identity, localization, layout, and icon changes are
  field- and build-dependent.
- PNG icon import and custom texture resources have a documented EML route but
  require fresh in-game visual verification.
- Visual resource substitution can be planned while preserving mechanics, but
  the model/material/placed-entity graph is not yet proven for arbitrary
  furniture. Plans now report declared dependencies and can flag unavailable
  resource GUIDs before runtime testing.

## Not proven / unsupported

- Lua cannot reliably inspect the contents of the Rust-backed ItemRegistry
  itemRefs array; apparent length growth is not catalog proof.
- Direct indexed writes to itemRefs are rejected by the runtime.
- Arbitrary original meshes, new enemy archetypes, new quest systems,
  animation systems, world generation, and multiplayer authority behavior are
  not supported by the current verified route.

## Release rule

No experimental route is promoted to stable until it has a unique manifest,
fresh EML session evidence, no donor overwrite, a reversible backup, and
in-game validation on the target build.

The shared capability audit enforces the same rule: runtime, visual, and
rollback evidence are all required before a capability can be labeled
verified.
