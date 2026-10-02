# EmberVault Control Center 0.1.0

## Included

- PySide6 and Qt Quick/QML desktop shell.
- Core game detection, settings, profiles, compatibility, logs, operations,
  and recovery services.
- Save Manager inspection, verified backup, re-verification, restore preview,
  safe restore, and post-restore verification.
- Profile-scoped package discovery, folder/ZIP import, enablement, compatibility
  diagnostics, dependency-aware enablement, safe removal, guarded deployment,
  ownership-protected undeploy, and read-only inspection of existing external
  `mod.json` mods.
- Staged Game Settings, Troubleshooter, Character projects, Research records
  with evidence lifecycle, Content projects, Knowledge search, and public
  catalog export.
- Guarded separate-process contracts for Trainer, Research, and Content Creator.

## Hardening included in the current build

- Guarded worker results use a versioned, read-only JSON contract and are
  rejected when their profile, operation, required fields, or output size do
  not match the launch context.
- Package and module discovery validates manifest identity, capabilities,
  lifecycle state, compatibility metadata, and portable executable paths.
- Package folder and ZIP imports reject symlinks, traversal, duplicate paths,
  oversized archives, and excessive entry counts.
- Live deployment requires an existing game directory, a conflict-free plan,
  symlink-free sources, and `package_type: "mod"`; failed deployments roll back
  newly created destinations.
- Catalog exports are deterministic and exclude local runtime paths and
  private research state.
- Restore requires a matching successful preview, and deployment requires a
  matching inspected plan before either operation can apply changes.
- Catalog handoffs include freshness metadata, a versioned tuning-adapter
  contract, a standalone verifier, and a repeatable repository sync command.
- Release verification validates the contents of packaged JSON contracts,
  manifests, and the seeded knowledge catalog, not only their filenames.
- The installed launcher smoke test asserts the shipped module and knowledge
  inventory before it exits.
- Module manifests explicitly declare `embedded` or `separate` process mode;
  contradictory launch declarations are rejected and the Modules workspace
  displays the boundary.
- Catalog export validation enforces the same process-mode rule before a local
  or public handoff is written.

## Important limitations

- Save Manager does not edit save contents.
- Staged Game Settings are not applied directly to a live game.
- Knowledge entries can be authored locally and remain searchable alongside
  the seeded safety catalog.
- The isolated tuning-audit worker can review staged settings and confirm the
  live game was not changed; it does not apply tuning.
- The experimental EML adapter now supports a guarded, owned-package lifecycle
  for the evidenced `BalancingTable.baseCritChance` field, including staged
  payloads, deployment, log readback, operation tracking, and rollback.
- Trainer and Content Creator gates now require an existing checksum-valid
  verified backup, not merely a backup identifier.
- Trainer plans enforce the same checksum-valid backup requirement at creation
  time and remain plan-only exports.
- Character projects remain planning metadata, not live mutations, and their
  planning notes can be revised safely. Content
  projects remain design-only locally, can track project-relative asset
  references, and a ready project may be explicitly
  published as a sanitized catalog summary, but no design brief or live game
  content is exposed or mutated.
- High-risk worker processes remain non-mutating in this release. Research
  performs a bounded evidence probe, Trainer performs a readiness audit, and
  Content Creator performs a design-boundary audit; all are terminated and
  audited if they exceed the worker timeout.
- Forums, moderation, and hosted community databases remain outside this
  desktop repository; validated catalog synchronization to the public
  EmberVault repository is implemented.

## Compatibility and isolation

- There is no hard-coded supported Enshrouded build range in 0.1.0. Packages
  declare the builds they have tested; the Control Center reports unknown,
  compatible, or incompatible status and blocks known-incompatible enablement.
- Normal package and settings workflows are embedded. Trainer, Research, and
  Content Creator use guarded separate-process contracts; their included
  workers cannot mutate live game or save data.
- Verified backups are stored under the runtime data directory in the Save
  Manager backup area. Restore requires a current-state backup and performs
  post-restore verification.

## Verification

The release baseline includes the Python unit suite, Python compilation, an
offscreen QML load check, wheel construction, isolated installed-prefix smoke
testing, and GitHub Actions verification on Ubuntu and Windows.
