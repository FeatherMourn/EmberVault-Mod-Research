# Multiplayer Admin Architecture v1

Multiplayer is a first-class **Toolkit** command category, not an assertion
about Enshrouded network internals. All current `multiplayer.*` commands are
registered as `unsupported` and fail closed.

## Pipeline

```text
F7 Multiplayer Admin → requester identity → Toolkit permission policy →
authority check → compatibility check → replication policy → feature module →
read-back / per-target result
```

Until stable session/player identity, host authority, and replication are
observed, the pipeline stops at `not_mapped`.

## Namespace

`multiplayer.status`, `players`, `safe_mode`, `player.*`, `permission.*`,
`quest.*`, `session.*`, `build.*`, and `world.*` are canonical registry
scaffolding. Metadata supplies category, subcategory, risk, authority,
permission key, and replication status to F7 and the palette.

## Quest completion scope

The default is **Vanilla**. Proposed Global/Shared and Individual policies are
not implemented. They require read-only evidence for acceptance, progress,
completion, rewards, persistence, replication, and host authority.

## Policy and safe mode

Future Toolkit roles: Host, Admin, Moderator, Builder, Player, Guest. Future
permission keys are Toolkit policy labels, not game permissions. Safe Mode will
keep diagnostics/read-only inspection available while disabling risky
multiplayer mutations.

## Milestone order

1. Read-only player/session discovery and stable identity.
2. Authority and replication mapping.
3. Read-only Player and Quest Inspectors.
4. Toolkit permission-policy layer.
5. One small host-authoritative action, only after verification.

Remote item/character edits, quest mutation, build enforcement, teleport, and
world-state mutation remain out of scope.
