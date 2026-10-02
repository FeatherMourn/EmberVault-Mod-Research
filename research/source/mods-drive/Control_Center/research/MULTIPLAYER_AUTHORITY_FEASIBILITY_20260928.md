# Multiplayer authority feasibility — 2026-09-28

## Scope

This report evaluates whether the verified EML/KFC route can safely create
multiplayer-authoritative content. It is a feasibility boundary, not a claim
that client-side resource registration is multiplayer-safe.

## Findings

| Area | Status | Current evidence/boundary |
|---|---|---|
| Client-side item/catalog registration | experimental | Runtime clone and UI registration work on the tested client build. |
| Server-owned item definitions | unsupported | No verified server resource-registration API is exposed by the current route. |
| Replication of custom resources | unsupported | No runtime evidence proves that another client receives or resolves a new resource. |
| Save persistence across peers | unverified | Single-client persistence has not established authoritative save behavior. |
| Permissions/ownership | unverified | Placement interaction exists for donor behavior; custom authority rules are not exposed. |
| Dedicated-server loading | unsupported | No compatible dedicated-server loader/API evidence exists in this project. |
| Anti-cheat and trust boundary | unsupported | Client patches cannot be treated as trusted server state. |

## Safe product policy

Control Center must label client-only modules as client-only and must not mark
them multiplayer-safe. A multiplayer claim requires a dedicated-server or
authoritative-host test showing registration, replication, persistence, and
permission behavior for the specific capability.

## Next research gate

Only proceed if an authoritative network-owned schema or supported server hook
is discovered. Start with a read-only inventory probe, isolate it from stable
profiles, and require peer-visible evidence before any mutation experiment.

## Conclusion

The current platform can continue developing single-player and client-side
content safely, but multiplayer authority remains unsupported through the
verified EML route. This boundary is explicit so future work cannot silently
promote client behavior into a multiplayer guarantee.
