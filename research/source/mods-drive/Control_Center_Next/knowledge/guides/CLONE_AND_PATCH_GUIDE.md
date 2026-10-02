# Clone-and-patch guide

Choose a donor, allocate collision-safe item and recipe IDs, clone before
editing, register the clone in the required registries, and add its UI entry by
cloning the containing typed set. Fixed-size arrays must not be appended to
directly. Verify vanilla preservation, duplicate prevention, and rollback in a
fresh isolated session.

The identity service persists deterministic IDs for repeated builds and can
also receive an explicit `occupied_ids` set from a current catalog or runtime
registry. It skips known occupied IDs when allocating a new identity and
fails closed if a previously assigned identity is later claimed by the
runtime. The local ownership file alone is not treated as a complete game
catalog.

Mechanic edits use an explicit allowlist (`comfort`, stack size, durability,
placement behavior, workstation, resource requirements, tags, category, unlock
state, and functional flags). They compile into a research-only plan until
same-build behavior and donor-isolation evidence promotes them; unknown
mechanic fields are rejected before packaging.
