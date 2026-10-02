# Capability Governance

The Control Center provides a read-only governance view over capability
promotion. Every capability is visible as `research-only`, `experimental`,
`verified`, or `stable`, with the evidence required for promotion shown beside
it.

Governance reports current-build evidence, reproducibility, runtime confirmation,
recovery testing, compatibility documentation, ownership, rollback testing,
promotion history, and missing requirements. Review actions do not mutate game
state. Promotion itself remains operation-tracked and continues to use the
fail-closed promotion contract.

Runtime adapters and mod compatibility remain evidence sources. Research owns
research evidence, Knowledge owns published explanations, Catalog Export owns
sanitized public records, and the Control Center coordinates review without
copying private evidence into the public catalog.
