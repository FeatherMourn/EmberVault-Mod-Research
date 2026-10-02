# Interaction schema inventory — build 1076226

Read-only source: the current `.cache/types.json` registry for build
`1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z`.

## Relevant reflected structures

- `keen::ecs::InteractionOffer`: default action, verb localization, override
  sequence, offer ID, verb ID, and offered-state fields.
- `keen::ecs::InteractionQuery`: query ID, radius, and offset.
- `keen::ecs::InteractionAcceptData`: guest ID, used item, and offer ID.
- `keen::ecs::InteractionLock`: required item, permission, amount, and
  daytime/toggle/water/buff lock structures.
- `keen::ecs::InteractionKnowledgeLock`: knowledge requirement and query.
- `keen::ecs::CraftingInteraction`: workstation, range properties, and comfort
  requirement fields.
- `keen::ecs::InteractionAttachment` and
  `keen::ecs::InteractionAttachmentGuest`: host/guest attachment state.
- `keen::ecs::DirectionalInteraction` and `InteractionToggle`: state, verb,
  sequence, and animation-state transitions.
- `keen::ecs::PickupItem`, `PickupItemZone`, and `ResourceNodePickupDrops`:
  pickup and drop-related structures.
- `keen::ecs::NpcInteractionTarget` and `NpcInteractionSequence`: NPC target
  and sequence-related structures.

## Classification

These are reflected ECS component/event schemas, not safely constructible EML
resource definitions. Their presence does not establish client/server
authority, persistence, or a route for attaching a new interaction to a cloned
furniture item. The interaction capability remains research-only.

The research installer treats the core offer/query/accept/event families as
unsafe probe targets. This prevents an ECS schema name from being passed to the
asset-resource API as though it were a normal KFC resource.

The extracted research tree contains interaction-bearing records only under
`TemplateResource` (for example, serialized
`keen::ecs::ClientInteractionOffer` and `keen::ecs::InteractionOffer` entries).
The current runtime has a recorded stall while resolving `TemplateResource`,
so these records are useful offline schema evidence but are not a safe donor
GUID for a live probe.

## Safe next gate

Use the generated `build_interaction_donor_probe.py` only after a future build
exposes an existing loaded interaction-bearing resource or item outside the
quarantined `TemplateResource` family. Do not create ECS components, emit
interaction events, or alter a saved world until an authoritative resource
owner and rollback boundary are identified.
