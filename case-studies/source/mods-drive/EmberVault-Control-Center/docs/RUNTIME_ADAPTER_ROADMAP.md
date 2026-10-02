# Runtime adapter roadmap

## EML — primary adapter

EML is the first supported runtime target because the existing research, Lua
API documentation, and content-development work are centered on it.

Before live mutation is enabled, the EML review packet must contain:

- exact Enshrouded build and EML build/API version;
- supported EML resource and configuration surfaces;
- one reproducible setting mapping;
- process and multiplayer scope;
- backup and rollback procedure;
- in-game readback or behavior evidence;
- clean-session and failure-session logs.

The first completed candidate is the evidenced `baseCritChance` field on
`keen::BalancingTable`, tested through the disposable Research-profile
workflow. Additional settings require their own evidence packet.

## Shroudtopia — future adapter

The current installation runs Shroudtopia and contains a working Mod Hub Lua
configuration surface. That evidence is retained for future support, but it is
not part of the first EML implementation.

Shroudtopia support must eventually have its own loader detection, manifest,
configuration mapping, backup rules, verification, and compatibility state. It
must not share undocumented assumptions with EML.

## Shared Control Center contract

Both adapters will implement the same contract: detect the loader, validate
the game build, stage values, create a verified recovery point, apply only
declared keys, record the operation, verify the result, roll back on failure,
and fail closed when evidence is incomplete.
