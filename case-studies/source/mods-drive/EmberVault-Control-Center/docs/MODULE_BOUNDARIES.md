# EmberVault module-boundary contract

Modules are independently packaged and discovered through a manifest. Each
manifest declares `process_mode` as `embedded` or `separate`; older metadata-only
manifests remain discoverable for compatibility but cannot be launched. The
Control Center renders normal, low-risk workflows in-process; higher-risk or
highly independent capabilities use a guarded worker process with an explicit
launch context and versioned result contract.

New modules should start from `templates/module/`. Its manifest records the
contract version, capability state, safety requirements, allowed profiles,
operation types, rollback behavior, and verification behavior. A module is not
ready for shell integration until those fields, its Core boundary, and its
tests are defined.

## Capability map

| Capability | Default execution | Release boundary |
| --- | --- | --- |
| `example` | Embedded | Demonstration module only |
| `tuning-audit` | Separate process | Read-only review of staged settings |
| `research` | Separate process | Bounded filesystem/evidence probe |
| `trainer` | Separate process | Backup-bound readiness audit; plan-only |
| `content-creator` | Separate process | Design-boundary audit; design-only |

## Embedded module rules

Embedded modules receive the Core launch context and must remain within the
capabilities declared by their manifest. They may read and update their own
managed records, but they must not bypass profile isolation, operation
tracking, package ownership checks, or Save Manager safety gates.

## Separate-process rules

Separate workers receive only the profile, operation, backup, game-path, and
manifest context required for their declared task. Their result must identify
the operation and profile, declare `read_only: true`, and satisfy the worker
result contract. The launcher rejects malformed, oversized, mismatched, or
mutating results and terminates workers that exceed their timeout.

## Promotion rule

A worker may not be promoted into a live mutation workflow merely because its
probe succeeds. Promotion requires current-build compatibility evidence, a
documented mutation scope, backup and recovery requirements, verification
steps, and a reviewed adapter or module contract.
