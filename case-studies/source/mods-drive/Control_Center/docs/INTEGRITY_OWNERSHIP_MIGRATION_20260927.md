# Integrity and Ownership Migration

The Control Center now treats installed content using explicit ownership and
integrity states rather than a single pass/fail flag.

| State | Meaning | Safe action |
| --- | --- | --- |
| `verified` | Recorded hashes match the installed files. | Continue using the package. |
| `updated_by_control_center` | The current ownership record was written by an approved Control Center deployment. | Upgrade or restore through the manager. |
| `user_modified` | A managed file differs from its recorded hash. | Inspect before repairing; do not overwrite silently. |
| `missing` | A recorded file is absent. | Restore the last backup or repair after review. |
| `untracked` | A manifest exists without a Control Center ownership record. | Adopt only after deliberate review, or leave untouched. |
| `quarantined` | A mod was moved to reversible quarantine storage. | Restore from the quarantine record when safe. |

Ownership records include the managed file hashes, the responsible writer,
previous deployment hashes, and a timestamped restore location. Experimental
probes remain separate from the stable active configuration and are not
silently adopted by the installer.

## Known external legacy modules

Some older third-party modules predate the Control Center manifest fields and
do not declare `feature_state` or an EML entrypoint. The live-loader can list a
documented module such as `flight_mod` as **known external** without changing
its files or claiming ownership. This is a diagnostic classification only:

- the module payload remains untouched;
- it is not treated as stable, experimental, or research-only Control Center
  content;
- isolation remains disabled until the module is deliberately reviewed,
  quarantined, or replaced with a compatible manifest;
- unknown legacy folders remain unclassified and continue to fail closed.

The verification suite covers helper-file hashes, changed files, missing
files, redeployment snapshots, failed redeployment rollback, restore points,
and reversible quarantine.
