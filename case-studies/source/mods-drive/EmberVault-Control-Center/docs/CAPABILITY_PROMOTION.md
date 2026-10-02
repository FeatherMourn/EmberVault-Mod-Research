# Capability promotion policy

Capabilities move only forward through `research-only`, `experimental`,
`verified`, and `stable`. A promotion decision is recorded by the Promotion
Service and exported without private evidence text.

Promotion beyond `research-only` requires all of the following:

- current game-build evidence;
- reproducible steps and results;
- runtime confirmation;
- recovery testing;
- compatibility documentation;
- a named owner; and
- tested rollback behavior.

The decision is auditable through Operations, visible in the Control Center,
and exposed to the public catalog as sanitized capability state. A module whose
manifest claims `verified` or `stable` cannot launch unless a matching
promotion decision exists. Promotion never grants permission to bypass profile,
backup, runtime, or process-isolation safety gates.
