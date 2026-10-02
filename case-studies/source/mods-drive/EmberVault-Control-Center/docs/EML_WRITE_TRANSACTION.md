# EML write transaction boundary

The Control Center now has a write-transaction gate, but the current adapter
is intentionally not enabled for live mutation.

The existing EML research proves an in-process Lua write/readback/restore on
`keen::BalancingTable.baseCritChance`. That is different from authorizing the
desktop application to modify the installed game or another mod's files.

Before enabling the transaction, the adapter needs an explicitly owned EML
package target with:

- a package manifest identifying EmberVault ownership;
- a declared input format and field mapping;
- an atomic staging and replacement procedure;
- a verified recovery point;
- a closed-game check;
- post-launch EML readback;
- automatic rollback when readback or launch validation fails.

Until those conditions exist, the executor fails closed with no file or game
mutation. The UI preview remains available for review.

## Staged payload

The adapter can render a transaction-specific Lua payload in memory. The
payload is tied to an operation ID, targets exactly one
`keen::BalancingTable`, and assigns only `baseCritChance`. It is not
automatically written to the installed game, and it is not a substitute for
post-launch readback or rollback.
