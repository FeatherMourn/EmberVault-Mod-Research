# Interaction donor search — build 1076226

## Search scope

The offline extracted research tree was searched for serialized
`InteractionOffer`, `ClientInteractionOffer`, and `CraftingInteraction`
records. The matching records were found under:

`H:\enshroudedresearch\item_test\TemplateResource\`

The current search result does not identify a safe, independently loadable
interaction resource family outside `TemplateResource`. The records are useful
for schema and dependency study, but they are not evidence that EML can load,
attach, persist, or replicate a new interaction.

## Safety verdict

- Candidate family: `keen::TemplateResource`
- Interaction-bearing records: serialized ECS offer records, including
  `keen::ecs::ClientInteractionOffer` and `keen::ecs::InteractionOffer`
- Runtime status: quarantined; controlled metadata resolution has stalled
- Safe live probe: not authorized by the current safety policy
- Custom-interaction status: research-only

## Promotion gate

Re-run this search after a game or EML build update. A live donor probe is only
eligible when the interaction-bearing resource resolves through a non-stalling
asset API route. Then use the generated read-only interaction-donor probe and
record authority, persistence, rollback, and replication separately.
