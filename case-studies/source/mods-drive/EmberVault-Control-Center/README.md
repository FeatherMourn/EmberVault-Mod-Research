# EmberVault Control Center

[![CI](https://github.com/FeatherMourn/EmberVault-Control-Center/actions/workflows/ci.yml/badge.svg)](https://github.com/FeatherMourn/EmberVault-Control-Center/actions/workflows/ci.yml)

The new modular desktop platform for managing, testing, and safely operating
Enshrouded mods and EmberVault packages.

This repository is being built from a clean architecture. The prior
`EnshroudedModHub` repository remains available as a reference source for
research, evidence, and selected proven service concepts.

## Current status

The first working vertical slice is in place. The Control Center currently
includes Home, Profiles, Save Manager safety workflows, profile-scoped package
management with guarded deployment/undeploy, staged Game Settings, read-only
Troubleshooter diagnostics, a safe Character Editor project layer, backup-bound
Trainer plans, Content Creator design projects, isolated Research records, and
a publish-controlled Knowledge catalog.

Read:

- [Architecture](docs/ARCHITECTURE.md)
- [Terminology contract](docs/TERMINOLOGY.md)
- [Module boundaries](docs/MODULE_BOUNDARIES.md)
- [Stage 0 Contracts](docs/STAGE_0_CONTRACTS.md)
- [Legacy Migration Inventory](docs/MIGRATION_INVENTORY.md)
- [User Guide](docs/USER_GUIDE.md)
- [Release Checklist](docs/RELEASE_CHECKLIST.md)
- [Roadmap Status](docs/ROADMAP_STATUS.md)
- [Full Staged Roadmap](docs/EMBERVAULT_ROADMAP.md)
- [Completion Audit](docs/COMPLETION_AUDIT.md)
- [Release Notes](docs/RELEASE_NOTES.md)

## Safety boundaries

Save Manager is inspection, backup, verification, restore preview, and safe
restore only. It does not directly edit save contents. Gameplay tuning and
higher-risk tools remain separate from normal embedded workflows and must use
explicit profiles, operation tracking, and recovery evidence.

## Development checks

Run the test suite with `python -m unittest discover -s tests -p "test*.py"`.
Install the project with `python -m pip install .`; this installs the PySide6
runtime dependency. The QML shell can then be smoke-tested with
`python -m control_center.app --smoke-test` using an offscreen Qt application.
