# Master Trainer GUI repair report

## Scope

The supplied `Cheat Tables/Enshrouded_Master_Trainer.CT` was treated as
read-only. Baseline and final SHA-256:

`0A591301A96C5FDF257564DEC6D53603EEFEC4AD7C79A3677BB7B3ECFA707D30`

## Findings and fixes

- The existing “Open Master Trainer” action used a hard-coded `F:` path that
  does not exist in this workspace. It now resolves the supplied CT relative
  to the project root.
- The action now parses the CT before opening it and reports the record count
  and a shortened identity hash in the status bar.
- Added `core/trainer_table.py`, a read-only XML inventory and hashing layer.
  It does not edit the CT, execute Auto Assembler text, or claim activation
  success.
- Added a parser regression test under `tests/test_trainer_table.py`.

## Verified table inventory

- 161 total records
- 66 Auto Assembler/script records
- 87 address/value records
- 8 group headers

## Connection and activation status

The repaired GUI can locate and open the original table and can identify its
contents. It does not yet provide a supported external Cheat Engine control
bridge, so no GUI toggle is presented as a verified enable/disable operation.
Activation state remains owned by Cheat Engine until a documented local bridge
is added and tested against a running offline game instance.

Teleport and editable-value controls are likewise not marked as connected by
this change; the CT inventory alone is not evidence that a pointer or value is
safe to write at runtime.

## Testing

- `py_compile` passed for the new parser and modified GUI.
- Direct parser smoke test passed against the supplied CT.
- `pytest` could not be run because `pytest` is not installed in the current
  Python environment.
