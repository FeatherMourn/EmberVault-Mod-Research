# Findings registry

This registry is intentionally conservative. A row is a research claim, not merely a file name. Add evidence links and build/version information before upgrading a claim's confidence.

| ID | Area | Finding | Status | Confidence | Build/version | Evidence |
|---|---|---|---|---|---|---|
| F-0001 | Research process | Runtime observations, static analysis, and implementation behavior must be recorded separately to avoid turning inference into fact. | Confirmed process rule | High | Repository-wide | `RECORD_TEMPLATE.md`, categorized source archive |
| F-0002 | Building and placement | The researched placement path and its known negative result are documented for revision 1076226; selection and final authority remain partly unresolved. | Strongly supported; runtime/version follow-up pending | Medium-high | 1076226 | [`records/BUILDING_PLACEMENT_1076226.md`](records/BUILDING_PLACEMENT_1076226.md) |
| F-0003 | Entities and observers | Reflected layouts, inventory action flow, and descriptor relationships are supported for 1076226, but no safe general-purpose cursor/entity observer target was recovered. | Strongly supported; runtime target unresolved | High for layouts; low-medium for hookability | 1076226 | [`records/ENTITIES_OBSERVERS_1076226.md`](records/ENTITIES_OBSERVERS_1076226.md) |
| F-0004 | Settings and administration | Game settings, admin actions, multiplayer behavior, and backend protocols are recurring research areas with implementation work attached. | Evidence present; synthesis pending | Medium | Multiple recorded builds | `../research/source/mods-drive/Architect_Mod/` |
| F-0005 | Data formats | KFC/reference extraction preserves provenance, unresolved references, and normalized building relationships for a recorded 1076226 bundle. | Confirmed for recorded inputs; portability pending | High | 1076226 | [`records/DATA_INGESTION_1076226.md`](records/DATA_INGESTION_1076226.md) |

## Status vocabulary

- **Confirmed** — reproduced or directly evidenced with a documented procedure.
- **Strongly supported** — multiple independent evidence paths agree, but a remaining runtime or version gap exists.
- **Working hypothesis** — plausible interpretation requiring a targeted experiment.
- **Evidence present; synthesis pending** — source material exists, but no canonical conclusion has been written yet.
- **Disproved/obsolete** — contradicted by later evidence or invalidated by a game update.
