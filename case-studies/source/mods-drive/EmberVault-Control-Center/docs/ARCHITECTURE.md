# EmberVault Control Center Architecture

## Product definition

EmberVault is a modular Enshrouded platform with one Control Center,
independently packaged capability modules, a protected research environment,
and first-class recovery services.

## Terminology

- **Control Center**: the EmberVault launcher and module-management application.
- **Module**: an independently packaged capability rendered inside Control Center or launched as a separate process when isolation is required.
- **EmberVault Core**: shared infrastructure and contracts used by Control Center and modules.
- **Mod**: a modification installed into Enshrouded.
- **Package**: a distributable module, mod, content package, or supporting component.
- **Profile**: a named configuration describing a particular Enshrouded and package setup.

## Boundaries

Control Center coordinates launch, installation, updates, health, profiles,
global settings, compatibility, and recovery actions. It does not directly
edit saves, characters, trainer state, or content projects.

Normal modules are independently packaged and initially embedded in the
Control Center shell. Trainer, Research, and possibly Content Creator may run
as separate processes with explicit contracts and isolated state.

Manifests with an `entrypoint` are loaded through the Core embedded-module
loader, which constrains the entrypoint to its package directory. Manifests with
an `executable` use the guarded separate-process launcher instead.

## First release boundary

Save Manager is inspection-, backup-, verification-, and restore-only. Direct
save editing and character mutation are outside the first release. Character
and content handoffs use explicit `plan-only` and `design-only` contracts.
Trainer session plans are also `plan-only`, require a checksum-valid recovery
backup, and do not execute trainer mutations.

## Technology

- Python platform services.
- PySide6 integration.
- Qt Quick/QML main shell.
- Windows-first packaging.
- Existing EnshroudedModHub retained as a reference and research source.
