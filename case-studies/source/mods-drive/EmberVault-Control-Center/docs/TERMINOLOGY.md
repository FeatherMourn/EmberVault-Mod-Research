# EmberVault terminology contract

This vocabulary is stable across the Control Center, embedded modules,
separate-process workers, catalog exports, and documentation.

## Product names

- **EmberVault** is the platform and public catalog brand.
- **EmberVault Control Center** is the desktop application.
- **EmberVault Core** is the shared service and contract layer.

The branded spelling is `EmberVault`. `EmbervaultRuntime` and the `embervault`
Python entry point remain compatibility identifiers and are not display names.

## Core nouns

- **Profile**: an isolated set of package enablement, staged settings, and
  research context. `default` is stable play; `research` is the experimental
  surface.
- **Package**: an independently installed artifact described by
  `package.json`. A package may be a mod, tuning adapter, or another module
  input, but only `package_type: "mod"` deploys to the game `mods` directory.
- **Module**: a contract-discovered capability that may render inside the
  Control Center or run as a guarded separate process.
- **Catalog**: a sanitized, portable public snapshot. It never contains local
  paths, save data, logs, profiles, or private research evidence.
- **Operation**: a tracked user action with a profile, status, and recovery
  context where applicable.

## Safety states

- **Verified**: the documented boundary and required evidence are satisfied.
- **Experimental**: controlled testing is possible, but promotion evidence is
  incomplete.
- **Research-only**: isolated or disposable-world work that must not enter a
  normal gameplay workflow.
- **Blocked**: a dependency, compatibility issue, unsafe boundary, or unresolved
  failure prevents the action.
- **Plan-only**: metadata describing a future character or trainer action; it
  does not mutate the game.
- **Design-only**: metadata describing future content; it does not create live
  game content.
- **Staged-only**: profile settings prepared for review or an adapter; they do
  not change the live game.

## Boundary rule

When a new capability does not fit these terms, its contract and safety state
must be clarified before it is added to the normal embedded workflow.
