# Stage 0 Contracts

## Core services

Initial EmberVault Core services:

- Game detection and path management.
- Settings and profiles.
- Structured logging.
- Operation tracking.
- Backup coordination.
- Compatibility evaluation.
- Module registry.
- Update infrastructure.
- Notifications.

## Communication rule

Modules request shared behavior through Core contracts. They do not reach into
another module's files, private state, or implementation details.

Example:

```text
Mods module → Core backup contract → Save Manager service
Troubleshooter → Core module registry
Content Creator → Core package contract → Mods module
```

## Compatibility states

Every package or capability must be classified as one of:

- compatible
- compatible-with-warnings
- unknown
- incompatible
- blocked

Unknown is a valid result and must not be silently treated as compatible.

## Operation identity

Every major mutation receives a durable operation ID and records its profile,
package, backup, start/end time, result, and relevant diagnostics.
