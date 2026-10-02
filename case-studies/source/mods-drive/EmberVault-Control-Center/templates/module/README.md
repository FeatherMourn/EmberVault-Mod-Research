# EmberVault module template

Copy this directory into `modules/<module-name>/`, then replace every
`replace-me` value before registering the module.

## Required decisions

- Choose an `id` beginning with `embervault.`.
- Declare the capability and feature state.
- Choose `embedded` or `separate` process mode.
- Describe safety requirements and allowed profiles.
- Describe rollback and verification behavior.
- List the operation types the module may record.
- Add backend wiring and a QML workspace only after the contract is stable.

## Delivery checklist

1. Validate the manifest against `contracts/module-manifest.schema.json`.
2. Implement the Core service boundary.
3. Register the module in the Control Center shell.
4. Track every action with an operation ID.
5. Enforce the declared safety and profile gates.
6. Implement recovery and verification behavior.
7. Add unit, failure, timeout, and packaging tests.
8. Add the sanitized catalog record if the module is public.
9. Document limitations and promotion requirements.
