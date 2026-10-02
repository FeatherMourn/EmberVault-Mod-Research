# CODE-0022B — Player Discovery static probe qualification

## Scope and result

This is an offline-only review of the installed Enshrouded executable and
reflection cache.  It did not attach to the game, inspect process memory, or
modify runtime code.

The reviewed executable is revision `1076226`, SHA-256
`AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`,
PE timestamp `0x6A4236C8`, image size `0x02DA7000`, image base
`0x140000000`.

**Decision: install zero player-discovery hooks.**  The current artifacts prove
several layouts, but do not provide a native function boundary that carries
both a vital component and defensible owner/entity identity.  Consequently no
candidate has the exact signature, unique match, understood overwritten
instructions, and semantic argument provenance required by the hook policy.

## Search method and negative evidence

The on-disk PE was parsed with `pefile` and its complete `.text` section
(`RVA 0x1000`, raw size `0x12A5200`) was decoded as x86-64 with Capstone.
The search located each exact ASCII type-name occurrence, tested every decoded
RIP-relative memory operand for a reference to it, then repeated the test for
up to three levels of embedded 64-bit image-VA and 32-bit RVA references.
No `.text` reference resolved to any reviewed `NetworkHealth`,
`NetworkStamina`, `keen::ecs::Health`, `keen::ecs::Stamina`, or
`keen::ecs::Mana` name occurrence.  This is negative evidence for these names
as direct native-xref anchors; it is not a claim that the types have no native
consumers.  Registration may use hashes or generated metadata not recoverable
from a name xref.

The relevant raw name occurrences map to these RVAs:

| Name | Exact executable RVAs |
|---|---|
| `NetworkHealth` | `0x1B7E990`, `0x1B7EA64`, `0x1B7EAE3`, `0x1CA11BF` |
| `NetworkStamina` | `0x1B7EEA8`, `0x1B7EF24`, `0x1B7EFCB`, `0x1CA186F` |
| `keen::ecs::Health` | `0x1B8DB58`, `0x1BE7440`, `0x1BFC450`, `0x1C0CED8`, `0x1C113A8` |
| `keen::ecs::Stamina` | `0x1BE7A40`, `0x1BE8330`, `0x1BE8BB8`, `0x1BFBE50`, `0x1C115F0`, `0x1C12100` |
| `keen::ecs::Mana` | `0x1BEA008`, `0x1BFC9C0`, `0x1C119E8` |

A potentially interesting diagnostic literal,
`[localPlayerId] Couldn't update Ambient query`, begins at RVA `0x14028B8`.
It also has no direct RIP-relative reference or resolvable three-level VA/RVA
pointer chain from `.text`.  A log string without its producer is not a
controlled-player observation point.

## Proven reflection facts

The source is the installed read-only `.cache/types.json` for this build.

| Type | Index | Layout | Attributes | Classification |
|---|---:|---|---|---|
| `keen::ecs::NetworkHealth` | 3038 | size `0x08`; `uint32 health +0x00`; `uint32 healthMax +0x04` | dynamic, do-not-save | `PROVEN_STATIC_BUILD_1076226` |
| `keen::ecs::NetworkStamina` | 3039 | size `0x04`; `uint16 stamina +0x00`; `uint16 staminaMax +0x02` | dynamic, do-not-save | `PROVEN_STATIC_BUILD_1076226` |
| `keen::ecs::Health` | 2442 | size `0x44`; definition `+0x14`; `sint32[8] dataStorage +0x24` | server-only, do-not-save | `PROVEN_STATIC_BUILD_1076226` |
| `keen::ecs::Stamina` | 2443 | same visible layout as Health | server-only, do-not-save | `PROVEN_STATIC_BUILD_1076226` |
| `keen::ecs::Mana` | 2450 | same visible layout as Health | server-only, do-not-save | `PROVEN_STATIC_BUILD_1076226` |
| `keen::ecs::StaminaDepletion` | 2585 | size `0x04`; `float accumulatedValue +0x00` | server-only, dynamic, do-not-save | `PROVEN_STATIC_BUILD_1076226` |
| `keen::ecs::HealthRecharge` | 2581 | size `0x10`; no visible fields | server-only | `PROVEN_STATIC_BUILD_1076226` |
| `keen::ecs::StaminaRecharge` | 2582 | size `0x10`; no visible fields | server-only | `PROVEN_STATIC_BUILD_1076226` |
| `keen::ecs::ManaRegeneration` | 2583 | size `0x10`; no visible fields | server-only | `PROVEN_STATIC_BUILD_1076226` |
| `keen::ecs::LocalPlayerMask` | 775 | size `0x01`; no visible fields | none exposed | `PROVEN_STATIC_BUILD_1076226` |
| `keen::ecs::IsLocalPlayerInRange` | 776 | size `0x08`; float margin `+0x00`; mask `+0x04` | dynamic, do-not-save | `PROVEN_STATIC_BUILD_1076226` |
| `keen::ecs::ClientPlayerStaminaHints` | 2812 | size `0x18`; three `Time` fields at `+0`, `+8`, `+0x10` | dynamic, do-not-save | `PROVEN_STATIC_BUILD_1076226` |

The duplicated `keen::ds::ecs` records have matching layouts.  The `server_only`
attribute separates the authoritative Health/Stamina/Mana family from the
network records at the type level.  The absence of `server_only` on a network
record does not prove a client instance, HUD use, ownership, or replication
direction.

The eight signed integers in `dataStorage` are opaque attribute storage.  No
slot is identified as current or maximum, so no `+0x24`-relative read is a
qualified vital observation.

## Candidate probe table

| Probe ID | Subsystem | Candidate function / RVA | Evidence source | Expected signature / overwritten instructions | Static interpretation | Runtime status | Classification | Contradictions / missing proof | Installed? / reason |
|---|---|---|---|---|---|---|---|---|---|
| `PD-LOCAL-INPUT-01` | Local player / input | Inventory action consumer `0x371810..0x37229F`; first pointer transition `0x37182C` | existing `ClientPlayerInput-StaticMap-v1` | At `0x37182C`: `48 8B 72 10` (`mov rsi,[rdx+0x10]`); at `0x371830`: `4C 8B E1`; at `0x371842`: `8B 46 08`; at `0x37184D`: `48 8B 4A 38` | Proven action-envelope consumer only | not active | `UNSOLVED` for local identity | RDX owner and concrete dispatch edge unresolved; action participation does not establish local controlled character; no safe detour span qualified at this inner transition | **No** — semantically insufficient even though instruction bytes are known |
| `PD-LOCAL-LOG-02` | Local player | unresolved producer for literal at `0x14028B8` | current PE string/xref scan | none; no code site recovered | Log implies some internal `localPlayerId` path exists | unavailable | `EXPERIMENTAL_STATIC_ANCHOR`; observation point `UNSOLVED` | no function, arguments, entity representation, signature, or overwritten instructions | **No** — metadata/log literal only |
| `PD-NETHEALTH-01` | Network health | none; name anchors listed above | current PE plus reflection | none | layout is proven; native consumer is not | unavailable | `UNSOLVED` | no direct or bounded pointer-chain `.text` xref; no owner/entity or side | **No** — no candidate site |
| `PD-NETSTAMINA-01` | Network stamina | none; name anchors listed above | current PE plus reflection | none | layout is proven; native consumer is not | unavailable | `UNSOLVED` | no direct or bounded pointer-chain `.text` xref; no owner/entity or side | **No** — no candidate site |
| `PD-ECS-HEALTH-01` | ECS Health | none | current PE plus reflection | none | server-only component layout proven | unavailable | `UNSOLVED` | `dataStorage` slot semantics and component owner unresolved | **No** — no candidate site |
| `PD-ECS-STAMINA-01` | ECS Stamina | none | current PE plus reflection | none | server-only component layout proven | unavailable | `UNSOLVED` | storage slots, ECS accessor/query, and owner unresolved | **No** — no candidate site |
| `PD-ECS-MANA-01` | ECS Mana | none | current PE plus reflection | none | server-only component layout proven; no NetworkMana was found | unavailable | `UNSOLVED` | no network analogue, slot semantics, accessor, query, or owner | **No** — no candidate site |
| `PD-STAMINA-DEPLETE-01` | Stamina behavior | none | reflection index 2585 | none | accumulated depletion is a behavioral lead, not current stamina | unavailable | `PROVEN_STATIC_BUILD_1076226` layout / `UNSOLVED` observer | could reflect many entities and cannot supply current/max | **No** — no native boundary or identity |
| `PD-CLIENT-SERVER-01` | Client/server correlation | none | reflected attributes | none | Health/Stamina/Mana are explicitly server-only; NetworkHealth/Stamina are dynamic records of unknown side/flow | unavailable | `UNSOLVED` | naming and attribute absence cannot prove replication source, destination, or matching entity | **No** — no paired observation sites |

## Hook qualification outcome

No row satisfies all required conditions:

1. a semantic current-build function/RVA;
2. an exact expected byte sequence that can be required uniquely;
3. a safely understood whole-instruction overwrite span;
4. a register/argument carrying the candidate structure;
5. a defensible owner/entity signal; and
6. a supported client/server interpretation.

Accordingly there is no hook/signature validation logic to add for these
subsystems.  Representing a zero RVA or empty signature as a disabled probe is
the correct fail-closed profile.

## Recommended next static experiment

Recover a generated ECS system/query descriptor (or a serializer descriptor)
that contains the numeric component identity for `NetworkHealth` or
`NetworkStamina`, then trace its registration callback to a concrete function.
Only promote it if the callback's calling convention and full overwritten
instruction span are independently understood.  For local identity, locate the
producer of the `localPlayerId` diagnostic through a hash/diagnostic registry or
an external disassembler's data-flow analysis; do not hook the known inventory
consumer merely because it processes player-originated input.
